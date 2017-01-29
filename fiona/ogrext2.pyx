# These are extension functions and classes using the OGR C API.


import datetime
import json
import locale
import logging
import os
import warnings
import math
import uuid

from six import integer_types, string_types, text_type

cimport ogrext2
from _geometry cimport (
    GeomBuilder, OGRGeomBuilder, geometry_type_code,
    normalize_geometry_type_code)
from fiona._err import cpl_errs
from fiona._geometry import GEOMETRY_TYPES
from fiona import compat
from fiona.errors import DriverError, SchemaError, CRSError, FionaValueError
from fiona.compat import OrderedDict
from fiona.rfc3339 import parse_date, parse_datetime, parse_time
from fiona.rfc3339 import FionaDateType, FionaDateTimeType, FionaTimeType

from libc.stdlib cimport malloc, free
from libc.string cimport strcmp
from cpython cimport PyBytes_FromStringAndSize, PyBytes_AsString


log = logging.getLogger("Fiona")
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
log.addHandler(NullHandler())


# Mapping of OGR integer field types to Fiona field type names.
#
# Lists are currently unsupported in this version, but might be done as
# arrays in a future version.

FIELD_TYPES = [
    'int',          # OFTInteger, Simple 32bit integer
    None,           # OFTIntegerList, List of 32bit integers
    'float',        # OFTReal, Double Precision floating point
    None,           # OFTRealList, List of doubles
    'str',          # OFTString, String of ASCII chars
    None,           # OFTStringList, Array of strings
    None,           # OFTWideString, deprecated
    None,           # OFTWideStringList, deprecated
    'bytes',        # OFTBinary, Raw Binary data
    'date',         # OFTDate, Date
    'time',         # OFTTime, Time
    'datetime',     # OFTDateTime, Date and Time
    'int',          # OFTInteger64, Single 64bit integer
    None,           # OFTInteger64List, List of 64bit integers
    ]

# Mapping of Fiona field type names to Python types.
FIELD_TYPES_MAP = {
    'int':      int,
    'float':    float,
    'str':      text_type,
    'date':     FionaDateType,
    'time':     FionaTimeType,
    'datetime': FionaDateTimeType,
    'bytes':    bytes,
   }

# OGR Driver capability
ODrCCreateDataSource = b"CreateDataSource"
ODrCDeleteDataSource = b"DeleteDataSource"

# OGR Layer capability
OLC_RANDOMREAD = b"RandomRead"
OLC_SEQUENTIALWRITE = b"SequentialWrite"
OLC_RANDOMWRITE = b"RandomWrite"
OLC_FASTSPATIALFILTER = b"FastSpatialFilter"
OLC_FASTFEATURECOUNT = b"FastFeatureCount"
OLC_FASTGETEXTENT = b"FastGetExtent"
OLC_FASTSETNEXTBYINDEX = b"FastSetNextByIndex"
OLC_CREATEFIELD = b"CreateField"
OLC_CREATEGEOMFIELD = b"CreateGeomField"
OLC_DELETEFIELD = b"DeleteField"
OLC_REORDERFIELDS = b"ReorderFields"
OLC_ALTERFIELDDEFN = b"AlterFieldDefn"
OLC_DELETEFEATURE = b"DeleteFeature"
OLC_STRINGSASUTF8 = b"StringsAsUTF8"
OLC_TRANSACTIONS = b"Transactions"

# OGR integer error types.

OGRERR_NONE = 0
OGRERR_NOT_ENOUGH_DATA = 1    # not enough data to deserialize */
OGRERR_NOT_ENOUGH_MEMORY = 2
OGRERR_UNSUPPORTED_GEOMETRY_TYPE = 3
OGRERR_UNSUPPORTED_OPERATION = 4
OGRERR_CORRUPT_DATA = 5
OGRERR_FAILURE = 6
OGRERR_UNSUPPORTED_SRS = 7
OGRERR_INVALID_HANDLE = 8


cdef char ** string_list(list_str):
    """
    Function by Stackoverflow User falsetru
    https://stackoverflow.com/questions/17511309/fast-string-array-cython
    """
    cdef char* s
    cdef char **ret = <char **>malloc(len(list_str) * sizeof(char *))
    for i in range(len(list_str)):
        s = list_str[i]
        ret[i] = s
    ret[i + 1] = NULL
    return ret

def _explode(coords):
    """Explode a GeoJSON geometry's coordinates object and yield
    coordinate tuples. As long as the input is conforming, the type of
    the geometry doesn't matter."""
    for e in coords:
        if isinstance(e, (float, int)):
            yield coords
            break
        else:
            for f in _explode(e):
                yield f


def _bounds(geometry):
    """Bounding box of a GeoJSON geometry"""
    try:
        xyz = tuple(zip(*list(_explode(geometry['coordinates']))))
        return min(xyz[0]), min(xyz[1]), max(xyz[0]), max(xyz[1])
    except (KeyError, TypeError):
        return None

def calc_gdal_version_num(maj, min, rev):
    """Calculates the internal gdal version number based on major, minor and revision"""
    return int(maj * 1000000 + min * 10000 + rev*100)

def get_gdal_version_num():
    """Return current internal version number of gdal"""
    return int(ogrext2.GDALVersionInfo("VERSION_NUM"))

def get_gdal_release_name():
    """Return release name of gdal"""
    return ogrext2.GDALVersionInfo("RELEASE_NAME")


# Feature extension classes and functions follow.

cdef class FeatureBuilder:
    """Build Fiona features from OGR feature pointers.

    No OGR objects are allocated by this function and the feature
    argument is not destroyed.
    """

    cdef build(self, void *feature, encoding='utf-8', bbox=False, driver=None):
        # The only method anyone ever needs to call
        cdef void *fdefn
        cdef int i
        cdef int y = 0
        cdef int m = 0
        cdef int d = 0
        cdef int hh = 0
        cdef int mm = 0
        cdef int ss = 0
        cdef int tz = 0
        cdef unsigned char *data
        cdef int l
        cdef int retval
        cdef char *key_c
        props = OrderedDict()
        for i in range(ogrext2.OGR_F_GetFieldCount(feature)):
            fdefn = ogrext2.OGR_F_GetFieldDefnRef(feature, i)
            if fdefn == NULL:
                raise ValueError("Null feature definition")
            key_c = ogrext2.OGR_Fld_GetNameRef(fdefn)
            if key_c == NULL:
                raise ValueError("Null field name reference")
            key_b = key_c
            key = key_b.decode(encoding)
            fieldtypename = FIELD_TYPES[ogrext2.OGR_Fld_GetType(fdefn)]
            if not fieldtypename:
                log.warning(
                    "Skipping field %s: invalid type %s",
                    key,
                    ogrext2.OGR_Fld_GetType(fdefn))
                continue

            # TODO: other types
            fieldtype = FIELD_TYPES_MAP[fieldtypename]
            if not ogrext2.OGR_F_IsFieldSet(feature, i):
                props[key] = None
            elif fieldtype is int:
                props[key] = ogrext2.OGR_F_GetFieldAsInteger64(feature, i)
            elif fieldtype is float:
                props[key] = ogrext2.OGR_F_GetFieldAsDouble(feature, i)

            elif fieldtype is text_type:
                try:
                    val = ogrext2.OGR_F_GetFieldAsString(feature, i)
                    val = val.decode(encoding)
                except UnicodeDecodeError:
                    log.warning(
                        "Failed to decode %s using %s codec", val, encoding)

                # Does the text contain a JSON object? Let's check.
                # Let's check as cheaply as we can.
                if driver == 'GeoJSON' and val.startswith('{'):
                    try:
                        val = json.loads(val)
                    except ValueError as err:
                        log.warning(str(err))

                # Now add to the properties object.
                props[key] = val

            elif fieldtype in (FionaDateType, FionaTimeType, FionaDateTimeType):
                retval = ogrext2.OGR_F_GetFieldAsDateTime(
                    feature, i, &y, &m, &d, &hh, &mm, &ss, &tz)
                try:
                    if fieldtype is FionaDateType:
                        props[key] = datetime.date(y, m, d).isoformat()
                    elif fieldtype is FionaTimeType:
                        props[key] = datetime.time(hh, mm, ss).isoformat()
                    else:
                        props[key] = datetime.datetime(
                            y, m, d, hh, mm, ss).isoformat()
                except ValueError as err:
                    log.exception(err)
                    props[key] = None

            elif fieldtype is bytes:
                data = ogrext2.OGR_F_GetFieldAsBinary(feature, i, &l)
                props[key] = data[:l]

            else:
                log.debug("%s: None, fieldtype: %r, %r" % (key, fieldtype, fieldtype in string_types))
                props[key] = None

        cdef void *cogr_geometry = ogrext2.OGR_F_GetGeometryRef(feature)
        if cogr_geometry is not NULL:
            geom = GeomBuilder().build(cogr_geometry)
        else:
            geom = None
        return {
            'type': 'Feature',
            'id': str(ogrext2.OGR_F_GetFID(feature)),
            'geometry': geom,
            'properties': props }


cdef class OGRFeatureBuilder:

    """Builds an OGR Feature from a Fiona feature mapping.

    Allocates one OGR Feature which should be destroyed by the caller.
    Borrows a layer definition from the collection.
    """

    cdef void * build(self, feature, collection) except NULL:
        cdef void *cogr_geometry = NULL
        cdef char *string_c
        cdef WritingSession session
        session = collection.session
        cdef void *cogr_layer = session.cogr_layer
        if cogr_layer == NULL:
            raise ValueError("Null layer")
        cdef void *cogr_featuredefn = ogrext2.OGR_L_GetLayerDefn(cogr_layer)
        if cogr_featuredefn == NULL:
            raise ValueError("Null feature definition")
        cdef void *cogr_feature = ogrext2.OGR_F_Create(cogr_featuredefn)
        if cogr_feature == NULL:
            raise ValueError("Null feature")

        if feature['geometry'] is not None:
            cogr_geometry = OGRGeomBuilder().build(
                                feature['geometry'])
        ogrext2.OGR_F_SetGeometryDirectly(cogr_feature, cogr_geometry)

        # OGR_F_SetFieldString takes UTF-8 encoded strings ('bytes' in
        # Python 3).
        encoding = session.get_internalencoding()

        for key, value in feature['properties'].items():
            log.debug(
                "Looking up %s in %s", key, repr(session._schema_mapping))
            ogr_key = session._schema_mapping[key]
            schema_type = collection.schema['properties'][key]
            try:
                key_bytes = ogr_key.encode(encoding)
            except UnicodeDecodeError:
                log.warning("Failed to encode %s using %s codec", key, encoding)
                key_bytes = ogr_key
            key_c = key_bytes
            i = ogrext2.OGR_F_GetFieldIndex(cogr_feature, key_c)
            if i < 0:
                continue

            # Special case: serialize dicts to assist OGR.
            if isinstance(value, dict):
                value = json.dumps(value)

            # Continue over the standard OGR types.
            if isinstance(value, integer_types):
                ogrext2.OGR_F_SetFieldInteger64(cogr_feature, i, value)
            elif isinstance(value, float):
                ogrext2.OGR_F_SetFieldDouble(cogr_feature, i, value)
            elif (isinstance(value, string_types)
            and schema_type in ['date', 'time', 'datetime']):
                if schema_type == 'date':
                    y, m, d, hh, mm, ss, ff = parse_date(value)
                elif schema_type == 'time':
                    y, m, d, hh, mm, ss, ff = parse_time(value)
                else:
                    y, m, d, hh, mm, ss, ff = parse_datetime(value)
                ogrext2.OGR_F_SetFieldDateTime(
                    cogr_feature, i, y, m, d, hh, mm, ss, 0)
            elif (isinstance(value, datetime.date)
            and schema_type == 'date'):
                y, m, d = value.year, value.month, value.day
                ogrext2.OGR_F_SetFieldDateTime(
                    cogr_feature, i, y, m, d, 0, 0, 0, 0)
            elif (isinstance(value, datetime.datetime)
            and schema_type == 'datetime'):
                y, m, d = value.year, value.month, value.day
                hh, mm, ss = value.hour, value.minute, value.second
                ogrext2.OGR_F_SetFieldDateTime(
                    cogr_feature, i, y, m, d, hh, mm, ss, 0)
            elif (isinstance(value, datetime.time)
            and schema_type == 'time'):
                hh, mm, ss = value.hour, value.minute, value.second
                ogrext2.OGR_F_SetFieldDateTime(
                    cogr_feature, i, 0, 0, 0, hh, mm, ss, 0)
            elif isinstance(value, string_types):
                try:
                    value_bytes = value.encode(encoding)
                except UnicodeDecodeError:
                    log.warning(
                        "Failed to encode %s using %s codec", value, encoding)
                    value_bytes = value
                string_c = value_bytes
                ogrext2.OGR_F_SetFieldString(cogr_feature, i, string_c)
            elif isinstance(value, bytes):
                string_c = value
                ogrext2.OGR_F_SetFieldBinary(cogr_feature, i, len(value),
                    <unsigned char*>string_c)
            elif value is None:
                pass # keep field unset/null
            else:
                raise ValueError("Invalid field type %s" % type(value))
            log.debug("Set field %s: %s" % (key, value))
        return cogr_feature


cdef _deleteOgrFeature(void *cogr_feature):
    """Delete an OGR feature"""
    if cogr_feature is not NULL:
        ogrext2.OGR_F_Destroy(cogr_feature)
    cogr_feature = NULL


def featureRT(feature, collection):
    # For testing purposes only, leaks the JSON data
    cdef void *cogr_feature = OGRFeatureBuilder().build(feature, collection)
    cdef void *cogr_geometry = ogrext2.OGR_F_GetGeometryRef(cogr_feature)
    if cogr_geometry == NULL:
        raise ValueError("Null geometry")
    log.debug("Geometry: %s" % ogrext2.OGR_G_ExportToJson(cogr_geometry))
    encoding = collection.encoding or 'utf-8'
    result = FeatureBuilder().build(
        cogr_feature,
        bbox=False,
        encoding=encoding,
        driver=collection.driver
    )
    _deleteOgrFeature(cogr_feature)
    return result


# Collection-related extension classes and functions

cdef class Session:

    cdef void *cogr_ds
    cdef void *cogr_layer
    cdef object _fileencoding
    cdef object _encoding
    cdef object collection

    def __init__(self):
        self.cogr_ds = NULL
        self.cogr_layer = NULL
        self._fileencoding = None
        self._encoding = None

    def __dealloc__(self):
        self.stop()

    def start(self, collection):
        cdef const char *path_c = NULL
        cdef const char *name_c = NULL
        cdef void *drv = NULL
        cdef void *ds = NULL
        cdef char ** drvs = NULL
        if collection.path == '-':
            path = '/vsistdin/'
        else:
            path = collection.path
        try:
            path_b = path.encode('utf-8')
        except UnicodeDecodeError:
            # Presume already a UTF-8 encoded string
            path_b = path
        path_c = path_b

        with cpl_errs:
            drivers = []
            if collection._driver:
                drivers = [collection._driver]
            elif collection.enabled_drivers:
                drivers = collection.enabled_drivers
            if drivers:
                for name in drivers:
                    name_b = name.encode()
                    name_c = name_b
                    log.debug("Trying driver: %s", name)
                    drv = ogrext2.GDALGetDriverByName(name_c)
                    if drv != NULL:
                        drvs = string_list([name_b])

                        flags = ogrext2.GDAL_OF_VECTOR | ogrext2.GDAL_OF_READONLY
                        log.debug("GDALOpenEx({}, {}, {})".format(path_c, flags, [name_b]))
                        ds = ogrext2.GDALOpenEx(path_c,
                                               flags,
                                               drvs,
                                               NULL,
                                               NULL)
                        free(drvs)
                    if ds != NULL:
                        self.cogr_ds = ds
                        collection._driver = name
                        _driver = ogrext2.GDALGetDatasetDriver(ds)
                        drv_name = ogrext2.GDALGetDriverShortName(_driver)
                        log.debug("Driver: {} Success".format(drv_name))

                        break
            else:
                self.cogr_ds = ogrext2.GDALOpenEx(path_c,
                                                 ogrext2.GDAL_OF_VECTOR | ogrext2.GDAL_OF_READONLY,
                                                 NULL,
                                                 NULL,
                                                 NULL)

        if self.cogr_ds == NULL:
            raise FionaValueError(
                "No dataset found at path '%s' using drivers: %s" % (
                    collection.path,
                    drivers or '*'))

        if isinstance(collection.name, string_types):
            name_b = collection.name.encode('utf-8')
            name_c = name_b
            self.cogr_layer = ogrext2.GDALDatasetGetLayerByName(
                                self.cogr_ds, name_c)
        elif isinstance(collection.name, int):
            self.cogr_layer = ogrext2.GDALDatasetGetLayer(
                                self.cogr_ds, collection.name)
            name_c = ogrext2.OGR_L_GetName(self.cogr_layer)
            name_b = name_c
            collection.name = name_b.decode('utf-8')

        if self.cogr_layer == NULL:
            raise ValueError("Null layer: " + repr(collection.name))

        self.collection = collection

        userencoding = self.collection.encoding
        if userencoding:
            ogrext2.CPLSetThreadLocalConfigOption('SHAPE_ENCODING', '')
            self._fileencoding = userencoding.upper()
        else:
            self._fileencoding = (
                ogrext2.OGR_L_TestCapability(
                    self.cogr_layer, OLC_STRINGSASUTF8) and
                'utf-8') or (
                self.get_driver() == "ESRI Shapefile" and
                'ISO-8859-1') or locale.getpreferredencoding().upper()

    def stop(self):
        self.cogr_layer = NULL
        if self.cogr_ds is not NULL:
            ogrext2.GDALClose(self.cogr_ds)
        self.cogr_ds = NULL

    def get_fileencoding(self):
        return self._fileencoding

    def get_internalencoding(self):
        if not self._encoding:
            fileencoding = self.get_fileencoding()
            self._encoding = (
                ogrext2.OGR_L_TestCapability(
                    self.cogr_layer, OLC_STRINGSASUTF8) and
                'utf-8') or fileencoding
        return self._encoding

    def get_length(self):
        if self.cogr_layer == NULL:
            raise ValueError("Null layer")
        return ogrext2.OGR_L_GetFeatureCount(self.cogr_layer, 0)

    def get_driver(self):
        cdef void *cogr_driver = ogrext2.GDALGetDatasetDriver(self.cogr_ds)
        if cogr_driver == NULL:
            raise ValueError("Null driver")
        cdef char *name = ogrext2.OGR_Dr_GetName(cogr_driver)
        driver_name = name
        return driver_name.decode()

    def get_schema(self):
        cdef int i
        cdef int n
        cdef void *cogr_featuredefn
        cdef void *cogr_fielddefn
        cdef char *key_c
        props = []

        if self.cogr_layer == NULL:
            raise ValueError("Null layer")

        cogr_featuredefn = ogrext2.OGR_L_GetLayerDefn(self.cogr_layer)
        if cogr_featuredefn == NULL:
            raise ValueError("Null feature definition")
        n = ogrext2.OGR_FD_GetFieldCount(cogr_featuredefn)
        for i from 0 <= i < n:
            cogr_fielddefn = ogrext2.OGR_FD_GetFieldDefn(cogr_featuredefn, i)
            if cogr_fielddefn == NULL:
                raise ValueError("Null field definition")
            key_c = ogrext2.OGR_Fld_GetNameRef(cogr_fielddefn)
            key_b = key_c
            if not bool(key_b):
                raise ValueError("Invalid field name ref: %s" % key)
            key = key_b.decode(self.get_internalencoding())
            fieldtypename = FIELD_TYPES[ogrext2.OGR_Fld_GetType(cogr_fielddefn)]
            if not fieldtypename:
                log.warning(
                    "Skipping field %s: invalid type %s",
                    key,
                    ogrext2.OGR_Fld_GetType(cogr_fielddefn))
                continue
            val = fieldtypename
            if fieldtypename == 'float':
                fmt = ""
                width = ogrext2.OGR_Fld_GetWidth(cogr_fielddefn)
                if width: # and width != 24:
                    fmt = ":%d" % width
                precision = ogrext2.OGR_Fld_GetPrecision(cogr_fielddefn)
                if precision: # and precision != 15:
                    fmt += ".%d" % precision
                val = "float" + fmt
            elif fieldtypename == 'int':
                fmt = ""
                width = ogrext2.OGR_Fld_GetWidth(cogr_fielddefn)
                if width: # and width != 11:
                    fmt = ":%d" % width
                val = fieldtypename + fmt
            elif fieldtypename == 'str':
                fmt = ""
                width = ogrext2.OGR_Fld_GetWidth(cogr_fielddefn)
                if width: # and width != 80:
                    fmt = ":%d" % width
                val = fieldtypename + fmt

            props.append((key, val))

        code = normalize_geometry_type_code(
            ogrext2.OGR_FD_GetGeomType(cogr_featuredefn))

        return {
            'properties': OrderedDict(props),
            'geometry': GEOMETRY_TYPES[code]}

    def get_crs(self):
        cdef char *proj_c = NULL
        cdef char *auth_key = NULL
        cdef char *auth_val = NULL
        cdef void *cogr_crs = NULL
        if self.cogr_layer == NULL:
            raise ValueError("Null layer")
        cogr_crs = ogrext2.OGR_L_GetSpatialRef(self.cogr_layer)
        crs = {}
        if cogr_crs is not NULL:
            log.debug("Got coordinate system")

            retval = ogrext2.OSRAutoIdentifyEPSG(cogr_crs)
            if retval > 0:
                log.info("Failed to auto identify EPSG: %d", retval)

            auth_key = ogrext2.OSRGetAuthorityName(cogr_crs, NULL)
            auth_val = ogrext2.OSRGetAuthorityCode(cogr_crs, NULL)

            if auth_key != NULL and auth_val != NULL:
                key_b = auth_key
                key = key_b.decode('utf-8')
                if key == 'EPSG':
                    val_b = auth_val
                    val = val_b.decode('utf-8')
                    crs['init'] = "epsg:" + val
            else:
                ogrext2.OSRExportToProj4(cogr_crs, &proj_c)
                if proj_c == NULL:
                    raise ValueError("Null projection")
                proj_b = proj_c
                log.debug("Params: %s", proj_b)
                value = proj_b.decode()
                value = value.strip()
                for param in value.split():
                    kv = param.split("=")
                    if len(kv) == 2:
                        k, v = kv
                        try:
                            v = float(v)
                            if v % 1 == 0:
                                v = int(v)
                        except ValueError:
                            # Leave v as a string
                            pass
                    elif len(kv) == 1:
                        k, v = kv[0], True
                    else:
                        raise ValueError("Unexpected proj parameter %s" % param)
                    k = k.lstrip("+")
                    crs[k] = v

            ogrext2.CPLFree(proj_c)
        else:
            log.debug("Projection not found (cogr_crs was NULL)")
        return crs

    def get_crs_wkt(self):
        cdef char *proj_c = NULL
        if self.cogr_layer == NULL:
            raise ValueError("Null layer")
        cogr_crs = ogrext2.OGR_L_GetSpatialRef(self.cogr_layer)
        crs_wkt = ""
        if cogr_crs is not NULL:
            log.debug("Got coordinate system")
            ogrext2.OSRExportToWkt(cogr_crs, &proj_c)
            if proj_c == NULL:
                raise ValueError("Null projection")
            proj_b = proj_c
            crs_wkt = proj_b.decode('utf-8')
            ogrext2.CPLFree(proj_c)
        else:
            log.debug("Projection not found (cogr_crs was NULL)")
        return crs_wkt

    def get_extent(self):
        if self.cogr_layer == NULL:
            raise ValueError("Null layer")
        cdef ogrext2.OGREnvelope extent
        result = ogrext2.OGR_L_GetExtent(self.cogr_layer, &extent, 1)
        return (extent.MinX, extent.MinY, extent.MaxX, extent.MaxY)

    def has_feature(self, fid):
        """Provides access to feature data by FID.

        Supports Collection.__contains__().
        """
        cdef void * cogr_feature
        fid = int(fid)
        cogr_feature = ogrext2.OGR_L_GetFeature(self.cogr_layer, fid)
        if cogr_feature != NULL:
            _deleteOgrFeature(cogr_feature)
            return True
        else:
            return False

    def get_feature(self, fid):
        """Provides access to feature data by FID.

        Supports Collection.__contains__().
        """
        cdef void * cogr_feature
        fid = int(fid)
        cogr_feature = ogrext2.OGR_L_GetFeature(self.cogr_layer, fid)
        if cogr_feature != NULL:
            _deleteOgrFeature(cogr_feature)
            return True
        else:
            return False


    def __getitem__(self, item):
        cdef void * cogr_feature
        if isinstance(item, slice):
            itr = Iterator(self.collection, item.start, item.stop, item.step)
            log.debug("Slice: %r", item)
            return list(itr)
        elif isinstance(item, int):
            index = item
            # from the back
            if index < 0:
                ftcount = ogrext2.OGR_L_GetFeatureCount(self.cogr_layer, 0)
                if ftcount == -1:
                    raise IndexError(
                        "collection's dataset does not support negative indexes")
                index += ftcount
            cogr_feature = ogrext2.OGR_L_GetFeature(self.cogr_layer, index)
            if cogr_feature == NULL:
                return None
            feature = FeatureBuilder().build(
                cogr_feature,
                bbox=False,
                encoding=self.get_internalencoding(),
                driver=self.collection.driver
            )
            _deleteOgrFeature(cogr_feature)
            return feature


    def isactive(self):
        if self.cogr_layer != NULL and self.cogr_ds != NULL:
            return 1
        else:
            return 0


cdef class WritingSession(Session):

    cdef object _schema_mapping

    def start(self, collection, **kwargs):
        cdef void *cogr_fielddefn
        cdef void *cogr_driver
        cdef void *cogr_ds
        cdef void *cogr_layer
        cdef void *cogr_srs = NULL
        cdef char **options = NULL
        self.collection = collection
        cdef char *path_c
        cdef char *driver_c
        cdef char *name_c
        cdef char *proj_c
        cdef char *fileencoding_c
        path = collection.path

        if collection.mode == 'a':
            if os.path.exists(path):
                try:
                    path_b = path.encode('utf-8')
                except UnicodeDecodeError:
                    path_b = path
                path_c = path_b
                with cpl_errs:
                    self.cogr_ds = ogrext2.GDALOpenEx(path_c,
                                                 ogrext2.GDAL_OF_VECTOR | ogrext2.GDAL_OF_UPDATE,
                                                 NULL,
                                                 NULL,
                                                 NULL)
                if self.cogr_ds == NULL:
                    raise RuntimeError("Failed to open %s" % path)

                cogr_driver = ogrext2.GDALGetDatasetDriver(self.cogr_ds)
                if cogr_driver == NULL:
                    raise ValueError("Null driver")

                if isinstance(collection.name, string_types):
                    name_b = collection.name.encode()
                    name_c = name_b
                    self.cogr_layer = ogrext2.GDALDatasetGetLayerByName(
                                        self.cogr_ds, name_c)
                elif isinstance(collection.name, int):
                    self.cogr_layer = ogrext2.GDALDatasetGetLayer(
                                        self.cogr_ds, collection.name)

                if self.cogr_layer == NULL:
                    raise RuntimeError(
                        "Failed to get layer %s" % collection.name)
            else:
                raise OSError("No such file or directory %s" % path)

            userencoding = self.collection.encoding
            self._fileencoding = (userencoding or (
                ogrext2.OGR_L_TestCapability(self.cogr_layer, OLC_STRINGSASUTF8) and
                'utf-8') or (
                self.get_driver() == "ESRI Shapefile" and
                'ISO-8859-1') or locale.getpreferredencoding()).upper()

        elif collection.mode == 'w':
            try:
                path_b = path.encode('utf-8')
            except UnicodeDecodeError:
                path_b = path
            path_c = path_b
            driver_b = collection.driver.encode()
            driver_c = driver_b

            # Creation options
            for k, v in kwargs.items():
                k, v = k.upper(), str(v).upper()
                key_b = k.encode('utf-8')
                val_b = v.encode('utf-8')
                key_c = key_b
                val_c = val_b
                options = ogrext2.CSLSetNameValue(options, key_c, val_c)
                log.debug("Option %r=%r\n", k, v)

            cogr_driver = ogrext2.GDALGetDriverByName(driver_c)
            if cogr_driver == NULL:
                raise ValueError("Null driver")

            if not os.path.exists(path):
                cogr_ds = ogrext2.GDALCreate(
                    cogr_driver, path_c, 0, 0, 0, ogrext2.GDT_Unknown, NULL)

            else:
                with cpl_errs:
                    cogr_ds = ogrext2.GDALOpenEx(path_c,
                                     ogrext2.GDAL_OF_VECTOR | ogrext2.GDAL_OF_UPDATE,
                                     NULL,
                                     NULL,
                                     NULL)
                if cogr_ds == NULL:
                    cogr_ds = ogrext2.GDALCreate(
                        cogr_driver,
                        path_c,
                        0,
                        0,
                        0,
                        ogrext2.GDT_Unknown,
                        NULL)

                elif collection.name is None:
                    ogrext2.GDALClose(cogr_ds)
                    cogr_ds == NULL
                    log.debug("Deleted pre-existing data at %s", path)
                    cogr_ds = ogrext2.GDALCreate(
                        cogr_driver,
                        path_c,
                        0,
                        0,
                        0,
                        ogrext2.GDT_Unknown,
                        NULL)

                else:
                    pass

            if cogr_ds == NULL:
                raise RuntimeError("Failed to open %s" % path)
            else:
                self.cogr_ds = cogr_ds

            # Set the spatial reference system from the crs given to the
            # collection constructor. We by-pass the crs_wkt and crs
            # properties because they aren't accessible until the layer
            # is constructed (later).
            col_crs = collection._crs_wkt or collection._crs
            if col_crs:
                cogr_srs = ogrext2.OSRNewSpatialReference(NULL)
                if cogr_srs == NULL:
                    raise ValueError("NULL spatial reference")
                # First, check for CRS strings like "EPSG:3857".
                if isinstance(col_crs, string_types):
                    proj_b = col_crs.encode('utf-8')
                    proj_c = proj_b
                    ogrext2.OSRSetFromUserInput(cogr_srs, proj_c)
                elif isinstance(col_crs, compat.DICT_TYPES):
                    # EPSG is a special case.
                    init = col_crs.get('init')
                    if init:
                        log.debug("Init: %s", init)
                        auth, val = init.split(':')
                        if auth.upper() == 'EPSG':
                            log.debug("Setting EPSG: %s", val)
                            ogrext2.OSRImportFromEPSG(cogr_srs, int(val))
                    else:
                        params = []
                        col_crs['wktext'] = True
                        for k, v in col_crs.items():
                            if v is True or (k in ('no_defs', 'wktext') and v):
                                params.append("+%s" % k)
                            else:
                                params.append("+%s=%s" % (k, v))
                        proj = " ".join(params)
                        log.debug("PROJ.4 to be imported: %r", proj)
                        proj_b = proj.encode('utf-8')
                        proj_c = proj_b
                        ogrext2.OSRImportFromProj4(cogr_srs, proj_c)
                else:
                    raise ValueError("Invalid CRS")

                # Fixup, export to WKT, and set the GDAL dataset's projection.
                ogrext2.OSRFixup(cogr_srs)

            # Figure out what encoding to use. The encoding parameter given
            # to the collection constructor takes highest precedence, then
            # 'iso-8859-1', then the system's default encoding as last resort.
            sysencoding = locale.getpreferredencoding()
            userencoding = collection.encoding
            self._fileencoding = (userencoding or (
                collection.driver == "ESRI Shapefile" and
                'ISO-8859-1') or sysencoding).upper()

            fileencoding = self.get_fileencoding()
            if fileencoding:
                fileencoding_b = fileencoding.encode()
                fileencoding_c = fileencoding_b
                options = ogrext2.CSLSetNameValue(options, "ENCODING", fileencoding_c)

            # Does the layer exist already? If so, we delete it.
            layer_count = ogrext2.GDALDatasetGetLayerCount(self.cogr_ds)
            layer_names = []
            for i in range(layer_count):
                cogr_layer = ogrext2.GDALDatasetGetLayer(cogr_ds, i)
                name_c = ogrext2.OGR_L_GetName(cogr_layer)
                name_b = name_c
                layer_names.append(name_b.decode('utf-8'))

            idx = -1
            if isinstance(collection.name, string_types):
                if collection.name in layer_names:
                    idx = layer_names.index(collection.name)
            elif isinstance(collection.name, int):
                if collection.name >= 0 and collection.name < layer_count:
                    idx = collection.name
            if idx >= 0:
                log.debug("Deleted pre-existing layer at %s", collection.name)
                ogrext2.GDALDatasetDeleteLayer(self.cogr_ds, idx)

            # Create the named layer in the datasource.
            name_b = collection.name.encode('utf-8')
            name_c = name_b
            self.cogr_layer = ogrext2.GDALDatasetCreateLayer(
                self.cogr_ds,
                name_c,
                cogr_srs,
                geometry_type_code(
                    collection.schema.get('geometry', 'Unknown')),
                options)

            if cogr_srs != NULL:
                ogrext2.OSRDestroySpatialReference(cogr_srs)
            if options != NULL:
                ogrext2.CSLDestroy(options)

            if self.cogr_layer == NULL:
                raise ValueError("Null layer")
            log.debug("Created layer")

            # Next, make a layer definition from the given schema properties,
            # which are an ordered dict since Fiona 1.0.1.
            for key, value in collection.schema['properties'].items():
                log.debug("Creating field: %s %s", key, value)

                # Convert 'long' to 'int'. See
                # https://github.com/Toblerity/Fiona/issues/101.
                if value == 'long':
                    value = 'int'

                # Is there a field width/precision?
                width = precision = None
                if ':' in value:
                    value, fmt = value.split(':')
                    if '.' in fmt:
                        width, precision = map(int, fmt.split('.'))
                    else:
                        width = int(fmt)

                field_type = FIELD_TYPES.index(value)
                # See https://trac.osgeo.org/gdal/wiki/rfc31_ogr_64
                if value == 'int' and (width is not None and width >= 10):
                    field_type = 12

                encoding = self.get_internalencoding()
                key_bytes = key.encode(encoding)

                cogr_fielddefn = ogrext2.OGR_Fld_Create(
                    key_bytes,
                    field_type)
                if cogr_fielddefn == NULL:
                    raise ValueError("Null field definition")
                if width:
                    ogrext2.OGR_Fld_SetWidth(cogr_fielddefn, width)
                if precision:
                    ogrext2.OGR_Fld_SetPrecision(cogr_fielddefn, precision)
                ogrext2.OGR_L_CreateField(self.cogr_layer, cogr_fielddefn, 1)
                ogrext2.OGR_Fld_Destroy(cogr_fielddefn)
            log.debug("Created fields")

        # Mapping of the Python collection schema to the munged
        # OGR schema.
        ogr_schema = self.get_schema()
        self._schema_mapping = dict(zip(
            collection.schema['properties'].keys(),
            ogr_schema['properties'].keys() ))

        log.debug("Writing started")

    def writerecs(self, records, collection):
        """Writes buffered records to OGR."""
        cdef void *cogr_driver
        cdef void *cogr_feature

        cdef void *cogr_layer = self.cogr_layer
        if cogr_layer == NULL:
            raise ValueError("Null layer")

        schema_geom_type = collection.schema['geometry']
        cogr_driver = ogrext2.GDALGetDatasetDriver(self.cogr_ds)
        if ogrext2.OGR_Dr_GetName(cogr_driver) == b"GeoJSON":
            def validate_geometry_type(rec):
                return True
        elif ogrext2.OGR_Dr_GetName(cogr_driver) == b"ESRI Shapefile" \
                and "Point" not in collection.schema['geometry']:
            schema_geom_type = collection.schema['geometry'].lstrip(
                "3D ").lstrip("Multi")
            def validate_geometry_type(rec):
                return rec['geometry'] is None or \
                rec['geometry']['type'].lstrip(
                    "3D ").lstrip("Multi") == schema_geom_type
        else:
            schema_geom_type = collection.schema['geometry'].lstrip("3D ")
            def validate_geometry_type(rec):
                return rec['geometry'] is None or \
                       rec['geometry']['type'].lstrip("3D ") == schema_geom_type

        schema_props_keys = set(collection.schema['properties'].keys())
        for record in records:
            log.debug("Creating feature in layer: %s" % record)
            # Validate against collection's schema.
            if set(record['properties'].keys()) != schema_props_keys:
                raise ValueError(
                    "Record does not match collection schema: %r != %r" % (
                        record['properties'].keys(),
                        list(schema_props_keys) ))
            if not validate_geometry_type(record):
                raise ValueError(
                    "Record's geometry type does not match "
                    "collection schema's geometry type: %r != %r" % (
                         record['geometry']['type'],
                         collection.schema['geometry'] ))

            cogr_feature = OGRFeatureBuilder().build(record, collection)
            result = ogrext2.OGR_L_CreateFeature(cogr_layer, cogr_feature)
            if result != OGRERR_NONE:
                raise RuntimeError("Failed to write record: %s" % record)
            _deleteOgrFeature(cogr_feature)

    def sync(self, collection):
        """Syncs OGR to disk."""
        cdef void *cogr_ds = self.cogr_ds
        cdef void *cogr_layer = self.cogr_layer
        if cogr_ds == NULL:
            raise ValueError("Null data source")
        log.debug("Syncing OGR to disk")

        ogrext2.GDALFlushCache(cogr_ds)


cdef class Iterator:

    """Provides iterated access to feature data.
    """

    # Reference to its Collection
    cdef collection
    cdef encoding
    cdef int next_index
    cdef stop
    cdef start
    cdef step
    cdef fastindex
    cdef stepsign

    def __cinit__(self, collection, start=None, stop=None, step=None,
                  bbox=None, mask=None):
        if collection.session is None:
            raise ValueError("I/O operation on closed collection")
        self.collection = collection
        cdef Session session
        cdef void *cogr_geometry
        session = self.collection.session
        cdef void *cogr_layer = session.cogr_layer
        if cogr_layer == NULL:
            raise ValueError("Null layer")
        ogrext2.OGR_L_ResetReading(cogr_layer)

        if bbox and mask:
            raise ValueError("mask and bbox can not be set together")

        if bbox:
            ogrext2.OGR_L_SetSpatialFilterRect(
                cogr_layer, bbox[0], bbox[1], bbox[2], bbox[3])
        elif mask:
            cogr_geometry = OGRGeomBuilder().build(mask)
            ogrext2.OGR_L_SetSpatialFilter(cogr_layer, cogr_geometry)
            ogrext2.OGR_G_DestroyGeometry(cogr_geometry)

        else:
            ogrext2.OGR_L_SetSpatialFilter(
                cogr_layer, NULL)
        self.encoding = session.get_internalencoding()

        self.fastindex = ogrext2.OGR_L_TestCapability(
            session.cogr_layer, OLC_FASTSETNEXTBYINDEX)

        ftcount = ogrext2.OGR_L_GetFeatureCount(session.cogr_layer, 0)
        if ftcount == -1 and ((start is not None and start < 0) or
                              (stop is not None and stop < 0)):
            raise IndexError(
                "collection's dataset does not support negative slice indexes")

        if stop is not None and stop < 0:
            stop += ftcount

        if start is None:
            start = 0
        if start is not None and start < 0:
            start += ftcount

        # step size
        if step is None:
            step = 1
        if step == 0:
            raise ValueError("slice step cannot be zero")
        if step < 0 and not self.fastindex:
            warnings.warn("Layer does not support" \
                    "OLCFastSetNextByIndex, negative step size may" \
                    " be slow", RuntimeWarning)
        self.stepsign = int(math.copysign(1, step))
        self.stop = stop
        self.start = start
        self.step = step

        self.next_index = start
        log.debug("Index: %d", self.next_index)
        ogrext2.OGR_L_SetNextByIndex(session.cogr_layer, self.next_index)


    def __iter__(self):
        return self


    def _next(self):
        """Internal method to set read cursor to next item"""

        cdef Session session
        session = self.collection.session

        # Check if next_index is valid
        if self.next_index < 0:
            raise StopIteration

        if self.stepsign == 1:
            if self.next_index < self.start or (self.stop is not None and self.next_index >= self.stop):
                raise StopIteration
        else:
            if self.next_index > self.start or (self.stop is not None and self.next_index <= self.stop):
                raise StopIteration


        # Set read cursor to next_item position
        if self.step > 1 and self.fastindex:
            ogrext2.OGR_L_SetNextByIndex(session.cogr_layer, self.next_index)

        elif self.step > 1 and not self.fastindex and not self.next_index == self.start:
            for _ in range(self.step - 1):
                # TODO rbuffat add test -> OGR_L_GetNextFeature increments cursor by 1, therefore self.step - 1 as one increment was performed when feature is read
                cogr_feature = ogrext2.OGR_L_GetNextFeature(session.cogr_layer)
                if cogr_feature == NULL:
                    raise StopIteration
        elif self.step > 1 and not self.fastindex and self.next_index == self.start:
            ogrext2.OGR_L_SetNextByIndex(session.cogr_layer, self.next_index)

        elif self.step == 0:
            # ogrext2.OGR_L_GetNextFeature increments read cursor by one
            pass
        elif self.step < 0:
            ogrext2.OGR_L_SetNextByIndex(session.cogr_layer, self.next_index)

        # set the next index
        self.next_index += self.step


    def __next__(self):
        cdef void * cogr_feature
        cdef Session session
        session = self.collection.session

        #Update read cursor
        self._next()

        # Get the next feature.
        cogr_feature = ogrext2.OGR_L_GetNextFeature(session.cogr_layer)
        if cogr_feature == NULL:
            raise StopIteration

        feature = FeatureBuilder().build(
            cogr_feature,
            bbox=False,
            encoding=self.encoding,
            driver=self.collection.driver
        )
        _deleteOgrFeature(cogr_feature)
        return feature


cdef class ItemsIterator(Iterator):

    def __next__(self):

        cdef long fid
        cdef void * cogr_feature
        cdef Session session
        session = self.collection.session

        #Update read cursor
        self._next()

        # Get the next feature.
        cogr_feature = ogrext2.OGR_L_GetNextFeature(session.cogr_layer)
        if cogr_feature == NULL:
            raise StopIteration


        fid = ogrext2.OGR_F_GetFID(cogr_feature)
        feature = FeatureBuilder().build(
            cogr_feature,
            bbox=False,
            encoding=self.encoding,
            driver=self.collection.driver
        )
        _deleteOgrFeature(cogr_feature)

        return fid, feature


cdef class KeysIterator(Iterator):

    def __next__(self):
        cdef long fid
        cdef void * cogr_feature
        cdef Session session
        session = self.collection.session

        #Update read cursor
        self._next()

        # Get the next feature.
        cogr_feature = ogrext2.OGR_L_GetNextFeature(session.cogr_layer)
        if cogr_feature == NULL:
            raise StopIteration

        fid = ogrext2.OGR_F_GetFID(cogr_feature)
        _deleteOgrFeature(cogr_feature)

        return fid


def _remove(path, driver=None):
    """Deletes an OGR data source
    """
    cdef void *cogr_driver
    cdef int result

    if driver is None:
        driver = 'ESRI Shapefile'

    cogr_driver = ogrext2.OGRGetDriverByName(driver.encode('utf-8'))
    if cogr_driver == NULL:
        raise ValueError("Null driver")

    if not ogrext2.OGR_Dr_TestCapability(cogr_driver, ODrCDeleteDataSource):
        raise RuntimeError("Driver does not support dataset removal operation")

    result = ogrext2.GDALDeleteDataset(cogr_driver, path.encode('utf-8'))
    if result != OGRERR_NONE:
        raise RuntimeError("Failed to remove data source {}".format(path))


def _listlayers(path):

    """Provides a list of the layers in an OGR data source.
    """

    cdef void *cogr_ds
    cdef void *cogr_layer
    cdef char *path_c
    cdef char *name_c

    # Open OGR data source.
    try:
        path_b = path.encode('utf-8')
    except UnicodeDecodeError:
        path_b = path
    path_c = path_b
    with cpl_errs:
        cogr_ds = ogrext2.GDALOpenEx(path_c,
             ogrext2.GDAL_OF_VECTOR | ogrext2.GDAL_OF_READONLY,
             NULL,
             NULL,
             NULL)
#         cogr_ds = ogrext2.OGROpen(path_c, 0, NULL)
    if cogr_ds == NULL:
        raise ValueError("No data available at path '%s'" % path)

    # Loop over the layers to get their names.
    layer_count = ogrext2.GDALDatasetGetLayerCount(cogr_ds)
    layer_names = []
    for i in range(layer_count):
        cogr_layer = ogrext2.GDALDatasetGetLayer(cogr_ds, i)
        name_c = ogrext2.OGR_L_GetName(cogr_layer)
        name_b = name_c
        layer_names.append(name_b.decode('utf-8'))

    # Close up data source.
    if cogr_ds is not NULL:
        ogrext2.GDALClose(cogr_ds)
    cogr_ds = NULL

    return layer_names

def buffer_to_virtual_file(bytesbuf):
    """Maps a bytes buffer to a virtual file.
    """
    vsi_filename = '/vsimem/{}'.format(uuid.uuid4().hex)
    vsi_cfilename = vsi_filename if not isinstance(vsi_filename, string_types) else vsi_filename.encode('utf-8')

    vsi_handle = ogrext2.VSIFileFromMemBuffer(vsi_cfilename, bytesbuf, len(bytesbuf), 0)
    if vsi_handle == NULL:
        raise OSError('failed to map buffer to file')
    if ogrext2.VSIFCloseL(vsi_handle) != 0:
        raise OSError('failed to close mapped file handle')

    return vsi_filename

def remove_virtual_file(vsi_filename):
    vsi_cfilename = vsi_filename if not isinstance(vsi_filename, string_types) else vsi_filename.encode('utf-8')
    return ogrext2.VSIUnlink(vsi_cfilename)
