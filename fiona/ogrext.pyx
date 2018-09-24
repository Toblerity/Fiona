# These are extension functions and classes using the OGR C API.

from __future__ import absolute_import

import datetime
import json
import locale
import logging
import os
import warnings
import math
import uuid
from collections import namedtuple

from six import integer_types, string_types, text_type

from fiona._shim cimport *

from fiona._geometry cimport (
    GeomBuilder, OGRGeomBuilder, geometry_type_code,
    normalize_geometry_type_code)
from fiona._err cimport exc_wrap_int, exc_wrap_pointer, exc_wrap_vsilfile

import fiona
from fiona._err import cpl_errs, FionaNullPointerError, CPLE_BaseError
from fiona._geometry import GEOMETRY_TYPES
from fiona import compat
from fiona.errors import (
    DriverError, DriverIOError, SchemaError, CRSError, FionaValueError,
    TransactionError, GeometryTypeValidationError, DatasetDeleteError)
from fiona.compat import OrderedDict
from fiona.rfc3339 import parse_date, parse_datetime, parse_time
from fiona.rfc3339 import FionaDateType, FionaDateTimeType, FionaTimeType
from fiona.schema import FIELD_TYPES, FIELD_TYPES_MAP, normalize_field_type
from fiona.path import vsi_path

from fiona._shim cimport is_field_null

from libc.stdlib cimport malloc, free
from libc.string cimport strcmp
from cpython cimport PyBytes_FromStringAndSize, PyBytes_AsString


log = logging.getLogger(__name__)

DEFAULT_TRANSACTION_SIZE = 20000

# OGR Driver capability
cdef const char * ODrCCreateDataSource = "CreateDataSource"
cdef const char * ODrCDeleteDataSource = "DeleteDataSource"

# OGR Layer capability
cdef const char * OLC_RANDOMREAD = "RandomRead"
cdef const char * OLC_SEQUENTIALWRITE = "SequentialWrite"
cdef const char * OLC_RANDOMWRITE = "RandomWrite"
cdef const char * OLC_FASTSPATIALFILTER = "FastSpatialFilter"
cdef const char * OLC_FASTFEATURECOUNT = "FastFeatureCount"
cdef const char * OLC_FASTGETEXTENT = "FastGetExtent"
cdef const char * OLC_FASTSETNEXTBYINDEX = "FastSetNextByIndex"
cdef const char * OLC_CREATEFIELD = "CreateField"
cdef const char * OLC_CREATEGEOMFIELD = "CreateGeomField"
cdef const char * OLC_DELETEFIELD = "DeleteField"
cdef const char * OLC_REORDERFIELDS = "ReorderFields"
cdef const char * OLC_ALTERFIELDDEFN = "AlterFieldDefn"
cdef const char * OLC_DELETEFEATURE = "DeleteFeature"
cdef const char * OLC_STRINGSASUTF8 = "StringsAsUTF8"
cdef const char * OLC_TRANSACTIONS = "Transactions"

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
    return int(GDALVersionInfo("VERSION_NUM"))

def get_gdal_release_name():
    """Return release name of gdal"""
    return GDALVersionInfo("RELEASE_NAME")

cdef int GDAL_VERSION_NUM = get_gdal_version_num()

GDALVersion = namedtuple("GDALVersion", ["major", "minor", "revision"])
def get_gdal_version_tuple():
    gdal_version_num = get_gdal_version_num()
    major = gdal_version_num // 1000000
    minor = (gdal_version_num - (major * 1000000)) // 10000
    revision = (gdal_version_num - (major * 1000000) - (minor * 10000)) // 100
    return GDALVersion(major, minor, revision)

# Feature extension classes and functions follow.

cdef class FeatureBuilder:
    """Build Fiona features from OGR feature pointers.

    No OGR objects are allocated by this function and the feature
    argument is not destroyed.
    """

    cdef build(self, void *feature, encoding='utf-8', bbox=False, driver=None,
               ignore_fields=None, ignore_geometry=False):
        """Build a Fiona feature object from an OGR feature

        Parameters
        ----------
        feature : void *
            The OGR feature # TODO: use a real typedef
        encoding : str
            The encoding of OGR feature attributes
        bbox : bool
            Not used
        driver : str
            OGR format driver name like 'GeoJSON'
        ignore_fields : sequence
            A sequence of field names that will be ignored and omitted
            in the Fiona feature properties
        ignore_geometry : bool
            Flag for whether the OGR geometry field is to be ignored

        Returns
        -------
        dict
        """
        cdef void *fdefn = NULL
        cdef int i
        cdef int y = 0
        cdef int m = 0
        cdef int d = 0
        cdef int hh = 0
        cdef int mm = 0
        cdef int ss = 0
        cdef int tz = 0
        cdef unsigned char *data = NULL
        cdef int l
        cdef int retval
        cdef int fieldsubtype
        cdef const char *key_c = NULL

        # Skeleton of the feature to be returned.
        fid = OGR_F_GetFID(feature)
        props = OrderedDict()
        fiona_feature = {
            "type": "Feature",
            "id": str(fid),
            "properties": props,
        }

        ignore_fields = set(ignore_fields or [])

        # Iterate over the fields of the OGR feature.
        for i in range(OGR_F_GetFieldCount(feature)):
            fdefn = OGR_F_GetFieldDefnRef(feature, i)
            if fdefn == NULL:
                raise ValueError("Null feature definition")
            key_c = OGR_Fld_GetNameRef(fdefn)
            if key_c == NULL:
                raise ValueError("Null field name reference")
            key_b = key_c
            key = key_b.decode(encoding)

            if key in ignore_fields:
                continue

            fieldtypename = FIELD_TYPES[OGR_Fld_GetType(fdefn)]
            fieldsubtype = get_field_subtype(fdefn)
            if not fieldtypename:
                log.warning(
                    "Skipping field %s: invalid type %s",
                    key,
                    OGR_Fld_GetType(fdefn))
                continue

            # TODO: other types
            fieldtype = FIELD_TYPES_MAP[fieldtypename]

            if is_field_null(feature, i):
                props[key] = None

            elif fieldtypename is 'int32':
                if fieldsubtype == OFSTBoolean:
                    props[key] = bool(OGR_F_GetFieldAsInteger(feature, i))
                else:
                    props[key] = OGR_F_GetFieldAsInteger(feature, i)

            elif fieldtype is int:
                if fieldsubtype == OFSTBoolean:
                    props[key] = bool(OGR_F_GetFieldAsInteger64(feature, i))
                else:
                    props[key] = OGR_F_GetFieldAsInteger64(feature, i)

            elif fieldtype is float:
                props[key] = OGR_F_GetFieldAsDouble(feature, i)

            elif fieldtype is text_type:
                try:
                    val = OGR_F_GetFieldAsString(feature, i)
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
                retval = OGR_F_GetFieldAsDateTime(
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
                data = OGR_F_GetFieldAsBinary(feature, i, &l)
                props[key] = data[:l]

            else:
                log.debug("%s: None, fieldtype: %r, %r" % (key, fieldtype, fieldtype in string_types))
                props[key] = None

        cdef void *cogr_geometry
        if not ignore_geometry:
            cogr_geometry = OGR_F_GetGeometryRef(feature)
            if cogr_geometry is not NULL:
                geom = GeomBuilder().build(cogr_geometry)
                fiona_feature["geometry"] = geom
            else:
                fiona_feature["geometry"] = None

        return fiona_feature


cdef class OGRFeatureBuilder:

    """Builds an OGR Feature from a Fiona feature mapping.

    Allocates one OGR Feature which should be destroyed by the caller.
    Borrows a layer definition from the collection.
    """

    cdef void * build(self, feature, collection) except NULL:
        cdef void *cogr_geometry = NULL
        cdef const char *string_c = NULL
        cdef WritingSession session
        session = collection.session
        cdef void *cogr_layer = session.cogr_layer
        if cogr_layer == NULL:
            raise ValueError("Null layer")
        cdef void *cogr_featuredefn = OGR_L_GetLayerDefn(cogr_layer)
        if cogr_featuredefn == NULL:
            raise ValueError("Null feature definition")
        cdef void *cogr_feature = OGR_F_Create(cogr_featuredefn)
        if cogr_feature == NULL:
            raise ValueError("Null feature")

        if feature['geometry'] is not None:
            cogr_geometry = OGRGeomBuilder().build(
                                feature['geometry'])
        OGR_F_SetGeometryDirectly(cogr_feature, cogr_geometry)

        # OGR_F_SetFieldString takes UTF-8 encoded strings ('bytes' in
        # Python 3).
        encoding = session.get_internalencoding()

        for key, value in feature['properties'].items():
            log.debug(
                "Looking up %s in %s", key, repr(session._schema_mapping))
            ogr_key = session._schema_mapping[key]

            schema_type = normalize_field_type(collection.schema['properties'][key])

            log.debug("Normalizing schema type for key %r in schema %r to %r", key, collection.schema['properties'], schema_type)

            try:
                key_bytes = ogr_key.encode(encoding)
            except UnicodeDecodeError:
                log.warning("Failed to encode %s using %s codec", key, encoding)
                key_bytes = ogr_key
            key_c = key_bytes
            i = OGR_F_GetFieldIndex(cogr_feature, key_c)
            if i < 0:
                continue

            # Special case: serialize dicts to assist OGR.
            if isinstance(value, dict):
                value = json.dumps(value)

            # Continue over the standard OGR types.
            if isinstance(value, integer_types):

                log.debug("Setting field %r, type %r, to value %r", i, schema_type, value)

                if schema_type == 'int32':
                    OGR_F_SetFieldInteger(cogr_feature, i, value)
                else:
                    OGR_F_SetFieldInteger64(cogr_feature, i, value)

            elif isinstance(value, float):
                OGR_F_SetFieldDouble(cogr_feature, i, value)
            elif (isinstance(value, string_types)
            and schema_type in ['date', 'time', 'datetime']):
                if schema_type == 'date':
                    y, m, d, hh, mm, ss, ff = parse_date(value)
                elif schema_type == 'time':
                    y, m, d, hh, mm, ss, ff = parse_time(value)
                else:
                    y, m, d, hh, mm, ss, ff = parse_datetime(value)
                OGR_F_SetFieldDateTime(
                    cogr_feature, i, y, m, d, hh, mm, ss, 0)
            elif (isinstance(value, datetime.date)
            and schema_type == 'date'):
                y, m, d = value.year, value.month, value.day
                OGR_F_SetFieldDateTime(
                    cogr_feature, i, y, m, d, 0, 0, 0, 0)
            elif (isinstance(value, datetime.datetime)
            and schema_type == 'datetime'):
                y, m, d = value.year, value.month, value.day
                hh, mm, ss = value.hour, value.minute, value.second
                OGR_F_SetFieldDateTime(
                    cogr_feature, i, y, m, d, hh, mm, ss, 0)
            elif (isinstance(value, datetime.time)
            and schema_type == 'time'):
                hh, mm, ss = value.hour, value.minute, value.second
                OGR_F_SetFieldDateTime(
                    cogr_feature, i, 0, 0, 0, hh, mm, ss, 0)
            elif isinstance(value, bytes) and schema_type == "bytes":
                string_c = value
                OGR_F_SetFieldBinary(cogr_feature, i, len(value),
                    <unsigned char*>string_c)
            elif isinstance(value, string_types):
                try:
                    value_bytes = value.encode(encoding)
                except UnicodeDecodeError:
                    log.warning(
                        "Failed to encode %s using %s codec", value, encoding)
                    value_bytes = value
                string_c = value_bytes
                OGR_F_SetFieldString(cogr_feature, i, string_c)
            elif value is None:
                set_field_null(cogr_feature, i)
            else:
                raise ValueError("Invalid field type %s" % type(value))
            log.debug("Set field %s: %r" % (key, value))
        return cogr_feature


cdef _deleteOgrFeature(void *cogr_feature):
    """Delete an OGR feature"""
    if cogr_feature is not NULL:
        OGR_F_Destroy(cogr_feature)
    cogr_feature = NULL


def featureRT(feature, collection):
    # For testing purposes only, leaks the JSON data
    cdef void *cogr_feature = OGRFeatureBuilder().build(feature, collection)
    cdef void *cogr_geometry = OGR_F_GetGeometryRef(cogr_feature)
    if cogr_geometry == NULL:
        raise ValueError("Null geometry")
    log.debug("Geometry: %s" % OGR_G_ExportToJson(cogr_geometry))
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

    def start(self, collection, **kwargs):
        cdef const char *path_c = NULL
        cdef const char *name_c = NULL
        cdef void *drv = NULL
        cdef void *ds = NULL
        cdef char **ignore_fields = NULL

        path_b = collection.path.encode('utf-8')

#        if collection.path == '-':
#            path = '/vsistdin/'
#        else:
#            path = collection.path
#        try:
#            path_b = path.encode('utf-8')
#        except UnicodeDecodeError:
#            # Presume already a UTF-8 encoded string
#            path_b = path
        path_c = path_b

        userencoding = kwargs.get('encoding')

        # We have two ways of specifying drivers to try. Resolve the
        # values into a single set of driver short names.
        if collection._driver:
            drivers = set([collection._driver])
        elif collection.enabled_drivers:
            drivers = set(collection.enabled_drivers)
        else:
            drivers = None

        self.cogr_ds = gdal_open_vector(path_c, 0, drivers, kwargs)

        if isinstance(collection.name, string_types):
            name_b = collection.name.encode('utf-8')
            name_c = name_b
            self.cogr_layer = GDALDatasetGetLayerByName(
                                self.cogr_ds, name_c)
        elif isinstance(collection.name, int):
            self.cogr_layer = GDALDatasetGetLayer(
                                self.cogr_ds, collection.name)
            name_c = OGR_L_GetName(self.cogr_layer)
            name_b = name_c
            collection.name = name_b.decode('utf-8')

        if self.cogr_layer == NULL:
            raise ValueError("Null layer: " + repr(collection.name))

        self._fileencoding = userencoding or (
            OGR_L_TestCapability(
                self.cogr_layer, OLC_STRINGSASUTF8) and
            'utf-8') or (
            self.get_driver() == "ESRI Shapefile" and
            'ISO-8859-1') or locale.getpreferredencoding().upper()

        if collection.ignore_fields:
            try:
                for name in collection.ignore_fields:
                    try:
                        name = name.encode(self._fileencoding)
                    except AttributeError:
                        raise TypeError("Ignored field \"{}\" has type \"{}\", expected string".format(name, name.__class__.__name__))
                    ignore_fields = CSLAddString(ignore_fields, <const char *>name)
                OGR_L_SetIgnoredFields(self.cogr_layer, ignore_fields)
            finally:
                CSLDestroy(ignore_fields)

        self.collection = collection

    def stop(self):
        self.cogr_layer = NULL
        if self.cogr_ds != NULL:
            GDALClose(self.cogr_ds)
        self.cogr_ds = NULL

    def get_fileencoding(self):
        return self._fileencoding

    def get_internalencoding(self):
        if not self._encoding:
            fileencoding = self.get_fileencoding()
            self._encoding = (
                OGR_L_TestCapability(
                    self.cogr_layer, OLC_STRINGSASUTF8) and
                'utf-8') or fileencoding
        return self._encoding

    def get_length(self):
        if self.cogr_layer == NULL:
            raise ValueError("Null layer")
        return OGR_L_GetFeatureCount(self.cogr_layer, 0)

    def get_driver(self):
        cdef void *cogr_driver = GDALGetDatasetDriver(self.cogr_ds)
        if cogr_driver == NULL:
            raise ValueError("Null driver")
        cdef const char *name = OGR_Dr_GetName(cogr_driver)
        driver_name = name
        return driver_name.decode()

    def get_schema(self):
        cdef int i
        cdef int n
        cdef void *cogr_featuredefn = NULL
        cdef void *cogr_fielddefn = NULL
        cdef const char *key_c
        props = []

        if self.cogr_layer == NULL:
            raise ValueError("Null layer")

        if self.collection.ignore_fields:
            ignore_fields = self.collection.ignore_fields
        else:
            ignore_fields = set()

        cogr_featuredefn = OGR_L_GetLayerDefn(self.cogr_layer)
        if cogr_featuredefn == NULL:
            raise ValueError("Null feature definition")

        n = OGR_FD_GetFieldCount(cogr_featuredefn)

        for i from 0 <= i < n:
            cogr_fielddefn = OGR_FD_GetFieldDefn(cogr_featuredefn, i)
            if cogr_fielddefn == NULL:
                raise ValueError("Null field definition")

            key_c = OGR_Fld_GetNameRef(cogr_fielddefn)
            key_b = key_c

            if not bool(key_b):
                raise ValueError("Invalid field name ref: %s" % key)

            key = key_b.decode(self.get_internalencoding())

            if key in ignore_fields:
                log.debug("By request, ignoring field %r", key)
                continue

            fieldtypename = FIELD_TYPES[OGR_Fld_GetType(cogr_fielddefn)]
            if not fieldtypename:
                log.warning(
                    "Skipping field %s: invalid type %s",
                    key,
                    OGR_Fld_GetType(cogr_fielddefn))
                continue

            val = fieldtypename
            if fieldtypename == 'float':
                fmt = ""
                width = OGR_Fld_GetWidth(cogr_fielddefn)
                if width: # and width != 24:
                    fmt = ":%d" % width
                precision = OGR_Fld_GetPrecision(cogr_fielddefn)
                if precision: # and precision != 15:
                    fmt += ".%d" % precision
                val = "float" + fmt
            elif fieldtypename in ('int32', 'int64'):
                fmt = ""
                width = OGR_Fld_GetWidth(cogr_fielddefn)
                if width:
                    fmt = ":%d" % width
                val = 'int' + fmt
            elif fieldtypename == 'str':
                fmt = ""
                width = OGR_Fld_GetWidth(cogr_fielddefn)
                if width:
                    fmt = ":%d" % width
                val = fieldtypename + fmt

            props.append((key, val))

        ret = {"properties": OrderedDict(props)}

        if not self.collection.ignore_geometry:
            code = normalize_geometry_type_code(
                OGR_FD_GetGeomType(cogr_featuredefn))
            ret["geometry"] = GEOMETRY_TYPES[code]

        return ret

    def get_crs(self):
        cdef char *proj_c = NULL
        cdef const char *auth_key = NULL
        cdef const char *auth_val = NULL
        cdef void *cogr_crs = NULL
        if self.cogr_layer == NULL:
            raise ValueError("Null layer")
        cogr_crs = OGR_L_GetSpatialRef(self.cogr_layer)
        crs = {}
        if cogr_crs is not NULL:
            log.debug("Got coordinate system")

            retval = OSRAutoIdentifyEPSG(cogr_crs)
            if retval > 0:
                log.info("Failed to auto identify EPSG: %d", retval)

            auth_key = OSRGetAuthorityName(cogr_crs, NULL)
            auth_val = OSRGetAuthorityCode(cogr_crs, NULL)

            if auth_key != NULL and auth_val != NULL:
                key_b = auth_key
                key = key_b.decode('utf-8')
                if key == 'EPSG':
                    val_b = auth_val
                    val = val_b.decode('utf-8')
                    crs['init'] = "epsg:" + val
            else:
                OSRExportToProj4(cogr_crs, &proj_c)
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

            CPLFree(proj_c)
        else:
            log.debug("Projection not found (cogr_crs was NULL)")
        return crs

    def get_crs_wkt(self):
        cdef char *proj_c = NULL
        if self.cogr_layer == NULL:
            raise ValueError("Null layer")
        cogr_crs = OGR_L_GetSpatialRef(self.cogr_layer)
        crs_wkt = ""
        if cogr_crs is not NULL:
            log.debug("Got coordinate system")
            OSRExportToWkt(cogr_crs, &proj_c)
            if proj_c == NULL:
                raise ValueError("Null projection")
            proj_b = proj_c
            crs_wkt = proj_b.decode('utf-8')
            CPLFree(proj_c)
        else:
            log.debug("Projection not found (cogr_crs was NULL)")
        return crs_wkt

    def get_extent(self):
        cdef OGREnvelope extent

        if self.cogr_layer == NULL:
            raise ValueError("Null layer")

        result = OGR_L_GetExtent(self.cogr_layer, &extent, 1)
        return (extent.MinX, extent.MinY, extent.MaxX, extent.MaxY)

    def has_feature(self, fid):
        """Provides access to feature data by FID.

        Supports Collection.__contains__().
        """
        cdef void * cogr_feature
        fid = int(fid)
        cogr_feature = OGR_L_GetFeature(self.cogr_layer, fid)
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
        cogr_feature = OGR_L_GetFeature(self.cogr_layer, fid)
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
                ftcount = OGR_L_GetFeatureCount(self.cogr_layer, 0)
                if ftcount == -1:
                    raise IndexError(
                        "collection's dataset does not support negative indexes")
                index += ftcount
            cogr_feature = OGR_L_GetFeature(self.cogr_layer, index)
            if cogr_feature == NULL:
                return None
            feature = FeatureBuilder().build(
                cogr_feature,
                bbox=False,
                encoding=self.get_internalencoding(),
                driver=self.collection.driver,
                ignore_fields=self.collection.ignore_fields,
                ignore_geometry=self.collection.ignore_geometry,
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
        cdef void *cogr_srs = NULL
        cdef char **options = NULL
        cdef const char *path_c = NULL
        cdef const char *driver_c = NULL
        cdef const char *name_c = NULL
        cdef const char *proj_c = NULL
        cdef const char *fileencoding_c = NULL
        cdef OGRFieldSubType field_subtype
        path = collection.path
        self.collection = collection

        userencoding = kwargs.get('encoding')

        if collection.mode == 'a':
            if os.path.exists(path):
                try:
                    path_b = path.encode('utf-8')
                except UnicodeDecodeError:
                    path_b = path
                path_c = path_b
                self.cogr_ds = gdal_open_vector(path_c, 1, None, kwargs)

                cogr_driver = GDALGetDatasetDriver(self.cogr_ds)
                if cogr_driver == NULL:
                    raise ValueError("Null driver")

                if isinstance(collection.name, string_types):
                    name_b = collection.name.encode()
                    name_c = name_b
                    self.cogr_layer = GDALDatasetGetLayerByName(
                                        self.cogr_ds, name_c)
                elif isinstance(collection.name, int):
                    self.cogr_layer = GDALDatasetGetLayer(
                                        self.cogr_ds, collection.name)

                if self.cogr_layer == NULL:
                    raise RuntimeError(
                        "Failed to get layer %s" % collection.name)
            else:
                raise OSError("No such file or directory %s" % path)

            self._fileencoding = (userencoding or (
                OGR_L_TestCapability(self.cogr_layer, OLC_STRINGSASUTF8) and
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


            cogr_driver = GDALGetDriverByName(driver_c)
            if cogr_driver == NULL:
                raise ValueError("Null driver")

            # Our most common use case is the creation of a new data
            # file and historically we've assumed that it's a file on
            # the local filesystem and queryable via os.path.
            #
            # TODO: remove the assumption.
            if not os.path.exists(path):
                log.debug("File doesn't exist. Creating a new one...")
                cogr_ds = gdal_create(cogr_driver, path_c, kwargs)

            # TODO: revisit the logic in the following blocks when we
            # change the assumption above.
            else:
                if collection.driver == "GeoJSON" and os.path.exists(path):
                    # manually remove geojson file as GDAL doesn't do this for us
                    os.unlink(path)
                try:
                    # attempt to open existing dataset in write mode
                    cogr_ds = gdal_open_vector(path_c, 1, None, kwargs)
                except DriverError:
                    # failed, attempt to create it
                    cogr_ds = gdal_create(cogr_driver, path_c, kwargs)
                else:
                    # check capability of creating a new layer in the existing dataset
                    capability = check_capability_create_layer(cogr_ds)
                    if GDAL_VERSION_NUM < 2000000 and collection.driver == "GeoJSON":
                        # GeoJSON driver tells lies about it's capability
                        capability = False
                    if not capability or collection.name is None:
                        # unable to use existing dataset, recreate it
                        GDALClose(cogr_ds)
                        cogr_ds = NULL
                        cogr_ds = gdal_create(cogr_driver, path_c, kwargs)

            self.cogr_ds = cogr_ds

            # Set the spatial reference system from the crs given to the
            # collection constructor. We by-pass the crs_wkt and crs
            # properties because they aren't accessible until the layer
            # is constructed (later).
            col_crs = collection._crs_wkt or collection._crs
            if col_crs:
                cogr_srs = OSRNewSpatialReference(NULL)
                if cogr_srs == NULL:
                    raise ValueError("NULL spatial reference")
                # First, check for CRS strings like "EPSG:3857".
                if isinstance(col_crs, string_types):
                    proj_b = col_crs.encode('utf-8')
                    proj_c = proj_b
                    OSRSetFromUserInput(cogr_srs, proj_c)
                elif isinstance(col_crs, compat.DICT_TYPES):
                    # EPSG is a special case.
                    init = col_crs.get('init')
                    if init:
                        log.debug("Init: %s", init)
                        auth, val = init.split(':')
                        if auth.upper() == 'EPSG':
                            log.debug("Setting EPSG: %s", val)
                            OSRImportFromEPSG(cogr_srs, int(val))
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
                        OSRImportFromProj4(cogr_srs, proj_c)
                else:
                    raise ValueError("Invalid CRS")

                # Fixup, export to WKT, and set the GDAL dataset's projection.
                OSRFixup(cogr_srs)

            # Figure out what encoding to use. The encoding parameter given
            # to the collection constructor takes highest precedence, then
            # 'iso-8859-1', then the system's default encoding as last resort.
            sysencoding = locale.getpreferredencoding()
            self._fileencoding = (userencoding or (
                collection.driver == "ESRI Shapefile" and
                'ISO-8859-1') or sysencoding).upper()

            # The ENCODING option makes no sense for some drivers and
            # will result in a warning. Fixing is a TODO.
            fileencoding = self.get_fileencoding()
            if fileencoding:
                fileencoding_b = fileencoding.encode('utf-8')
                fileencoding_c = fileencoding_b
                with cpl_errs:
                    options = CSLSetNameValue(options, "ENCODING", fileencoding_c)

            # Does the layer exist already? If so, we delete it.
            layer_count = GDALDatasetGetLayerCount(self.cogr_ds)
            layer_names = []
            for i in range(layer_count):
                cogr_layer = GDALDatasetGetLayer(cogr_ds, i)
                name_c = OGR_L_GetName(cogr_layer)
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
                GDALDatasetDeleteLayer(self.cogr_ds, idx)

            # Create the named layer in the datasource.
            name_b = collection.name.encode('utf-8')
            name_c = name_b

            for k, v in kwargs.items():
                k = k.upper().encode('utf-8')
                if isinstance(v, bool):
                    v = ('ON' if v else 'OFF').encode('utf-8')
                else:
                    v = str(v).encode('utf-8')
                log.debug("Set option %r: %r", k, v)
                options = CSLAddNameValue(options, <const char *>k, <const char *>v)

            geometry_type = collection.schema.get("geometry", "Unknown")
            if not isinstance(geometry_type, string_types) and geometry_type is not None:
                geometry_types = set(geometry_type)
                if len(geometry_types) > 1:
                    geometry_type = "Unknown"
                else:
                    geometry_type = geometry_types.pop()
            if geometry_type == "Any" or geometry_type is None:
                geometry_type = "Unknown"
            geometry_code = geometry_type_code(geometry_type)

            try:
                self.cogr_layer = exc_wrap_pointer(
                    GDALDatasetCreateLayer(
                        self.cogr_ds, name_c, cogr_srs,
                        geometry_code, options))
            except Exception as exc:
                raise DriverIOError(str(exc))
            finally:
                if options != NULL:
                    CSLDestroy(options)

                # Shapefile layers make a copy of the passed srs. GPKG
                # layers, on the other hand, increment its reference
                # count. OSRRelease() is the safe way to release
                # OGRSpatialReferenceH.
                if cogr_srs != NULL:
                    OSRRelease(cogr_srs)

            if self.cogr_layer == NULL:
                raise ValueError("Null layer")

            log.debug("Created layer %s", collection.name)

            # Next, make a layer definition from the given schema properties,
            # which are an ordered dict since Fiona 1.0.1.
            for key, value in collection.schema['properties'].items():

                log.debug("Begin creating field: %r value: %r", key, value)

                field_subtype = OFSTNone

                # Convert 'long' to 'int'. See
                # https://github.com/Toblerity/Fiona/issues/101.
                if fiona.gdal_version.major >= 2 and value in ('int', 'long'):
                    value = 'int64'
                elif value == 'int':
                    value = 'int32'

                if value == 'bool':
                    value = 'int32'
                    field_subtype = OFSTBoolean

                # Is there a field width/precision?
                width = precision = None
                if ':' in value:
                    value, fmt = value.split(':')

                    log.debug("Field format parsing, value: %r, fmt: %r", value, fmt)

                    if '.' in fmt:
                        width, precision = map(int, fmt.split('.'))
                    else:
                        width = int(fmt)

                    if value == 'int':
                        if GDAL_VERSION_NUM >= 2000000 and (width == 0 or width >= 10):
                            value = 'int64'
                        else:
                            value = 'int32'

                field_type = FIELD_TYPES.index(value)
                encoding = self.get_internalencoding()
                key_bytes = key.encode(encoding)

                cogr_fielddefn = exc_wrap_pointer(OGR_Fld_Create(key_bytes, field_type))

                if cogr_fielddefn == NULL:
                    raise ValueError("Field {} definition is NULL".format(key))

                if width:
                    OGR_Fld_SetWidth(cogr_fielddefn, width)
                if precision:
                    OGR_Fld_SetPrecision(cogr_fielddefn, precision)
                if field_subtype != OFSTNone:
                    # subtypes are new in GDAL 2.x, ignored in 1.x
                    set_field_subtype(cogr_fielddefn, field_subtype)

                try:
                    exc_wrap_int(OGR_L_CreateField(self.cogr_layer, cogr_fielddefn, 1))
                except CPLE_BaseError as exc:
                    raise SchemaError(str(exc))

                OGR_Fld_Destroy(cogr_fielddefn)

                log.debug("End creating field %r", key)

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
        cdef int features_in_transaction = 0

        cdef void *cogr_layer = self.cogr_layer
        if cogr_layer == NULL:
            raise ValueError("Null layer")

        schema_geom_type = collection.schema['geometry']
        cogr_driver = GDALGetDatasetDriver(self.cogr_ds)
        driver_name = OGR_Dr_GetName(cogr_driver).decode("utf-8")

        valid_geom_types = collection._valid_geom_types
        def validate_geometry_type(record):
            if record["geometry"] is None:
                return True
            return record["geometry"]["type"].lstrip("3D ") in valid_geom_types

        log.debug("Starting transaction (initial)")
        result = gdal_start_transaction(self.cogr_ds, 0)
        if result == OGRERR_FAILURE:
            raise TransactionError("Failed to start transaction")

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
                raise GeometryTypeValidationError(
                    "Record's geometry type does not match "
                    "collection schema's geometry type: %r != %r" % (
                         record['geometry']['type'],
                         collection.schema['geometry'] ))

            cogr_feature = OGRFeatureBuilder().build(record, collection)
            result = OGR_L_CreateFeature(cogr_layer, cogr_feature)
            if result != OGRERR_NONE:
                raise RuntimeError("Failed to write record: %s" % record)
            _deleteOgrFeature(cogr_feature)

            features_in_transaction += 1
            if features_in_transaction == DEFAULT_TRANSACTION_SIZE:
                log.debug("Comitting transaction (intermediate)")
                result = gdal_commit_transaction(self.cogr_ds)
                if result == OGRERR_FAILURE:
                    raise TransactionError("Failed to commit transaction")
                log.debug("Starting transaction (intermediate)")
                result = gdal_start_transaction(self.cogr_ds, 0)
                if result == OGRERR_FAILURE:
                    raise TransactionError("Failed to start transaction")
                features_in_transaction = 0

        log.debug("Comitting transaction (final)")
        result = gdal_commit_transaction(self.cogr_ds)
        if result == OGRERR_FAILURE:
            raise TransactionError("Failed to commit transaction")

    def sync(self, collection):
        """Syncs OGR to disk."""
        cdef void *cogr_ds = self.cogr_ds
        cdef void *cogr_layer = self.cogr_layer
        if cogr_ds == NULL:
            raise ValueError("Null data source")


        gdal_flush_cache(cogr_ds)
        log.debug("Flushed data source cache")

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
        OGR_L_ResetReading(cogr_layer)

        if bbox and mask:
            raise ValueError("mask and bbox can not be set together")

        if bbox:
            OGR_L_SetSpatialFilterRect(
                cogr_layer, bbox[0], bbox[1], bbox[2], bbox[3])
        elif mask:
            cogr_geometry = OGRGeomBuilder().build(mask)
            OGR_L_SetSpatialFilter(cogr_layer, cogr_geometry)
            OGR_G_DestroyGeometry(cogr_geometry)

        else:
            OGR_L_SetSpatialFilter(
                cogr_layer, NULL)
        self.encoding = session.get_internalencoding()

        self.fastindex = OGR_L_TestCapability(
            session.cogr_layer, OLC_FASTSETNEXTBYINDEX)

        ftcount = OGR_L_GetFeatureCount(session.cogr_layer, 0)
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
        OGR_L_SetNextByIndex(session.cogr_layer, self.next_index)


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
            OGR_L_SetNextByIndex(session.cogr_layer, self.next_index)

        elif self.step > 1 and not self.fastindex and not self.next_index == self.start:
            for _ in range(self.step - 1):
                # TODO rbuffat add test -> OGR_L_GetNextFeature increments cursor by 1, therefore self.step - 1 as one increment was performed when feature is read
                cogr_feature = OGR_L_GetNextFeature(session.cogr_layer)
                if cogr_feature == NULL:
                    raise StopIteration
        elif self.step > 1 and not self.fastindex and self.next_index == self.start:
            OGR_L_SetNextByIndex(session.cogr_layer, self.next_index)

        elif self.step == 0:
            # OGR_L_GetNextFeature increments read cursor by one
            pass
        elif self.step < 0:
            OGR_L_SetNextByIndex(session.cogr_layer, self.next_index)

        # set the next index
        self.next_index += self.step


    def __next__(self):
        cdef void * cogr_feature
        cdef Session session
        session = self.collection.session

        #Update read cursor
        self._next()

        # Get the next feature.
        cogr_feature = OGR_L_GetNextFeature(session.cogr_layer)
        if cogr_feature == NULL:
            raise StopIteration

        feature = FeatureBuilder().build(
            cogr_feature,
            bbox=False,
            encoding=self.encoding,
            driver=self.collection.driver,
            ignore_fields=self.collection.ignore_fields,
            ignore_geometry=self.collection.ignore_geometry,
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
        cogr_feature = OGR_L_GetNextFeature(session.cogr_layer)
        if cogr_feature == NULL:
            raise StopIteration


        fid = OGR_F_GetFID(cogr_feature)
        feature = FeatureBuilder().build(
            cogr_feature,
            bbox=False,
            encoding=self.encoding,
            driver=self.collection.driver,
            ignore_fields=self.collection.ignore_fields,
            ignore_geometry=self.collection.ignore_geometry,
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
        cogr_feature = OGR_L_GetNextFeature(session.cogr_layer)
        if cogr_feature == NULL:
            raise StopIteration

        fid = OGR_F_GetFID(cogr_feature)
        _deleteOgrFeature(cogr_feature)

        return fid


def _remove(path, driver=None):
    """Deletes an OGR data source
    """
    cdef void *cogr_driver
    cdef void *cogr_ds
    cdef int result
    cdef char *driver_c

    if driver is None:
        # attempt to identify the driver by opening the dataset
        try:
            cogr_ds = gdal_open_vector(path.encode("utf-8"), 0, None, {})
        except (DriverError, FionaNullPointerError):
            raise DatasetDeleteError("Failed to remove data source {}".format(path))
        cogr_driver = GDALGetDatasetDriver(cogr_ds)
        GDALClose(cogr_ds)
    else:
        cogr_driver = OGRGetDriverByName(driver.encode("utf-8"))

    if cogr_driver == NULL:
        raise DatasetDeleteError("Null driver when attempting to delete {}".format(path))

    if not OGR_Dr_TestCapability(cogr_driver, ODrCDeleteDataSource):
        raise DatasetDeleteError("Driver does not support dataset removal operation")

    result = GDALDeleteDataset(cogr_driver, path.encode('utf-8'))
    if result != OGRERR_NONE:
        raise DatasetDeleteError("Failed to remove data source {}".format(path))


def _remove_layer(path, layer, driver=None):
    cdef void *cogr_ds
    cdef int layer_index
    
    if isinstance(layer, integer_types):
        layer_index = layer
        layer_str = str(layer_index)
    else:
        layer_names = _listlayers(path)
        try:
            layer_index = layer_names.index(layer)
        except ValueError:
            raise ValueError("Layer \"{}\" does not exist in datasource: {}".format(layer, path))
        layer_str = '"{}"'.format(layer)
    
    if layer_index < 0:
        layer_names = _listlayers(path)
        layer_index = len(layer_names) + layer_index
    
    try:
        cogr_ds = gdal_open_vector(path.encode("utf-8"), 1, None, {})
    except (DriverError, FionaNullPointerError):
        raise DatasetDeleteError("Failed to remove data source {}".format(path))

    result = OGR_DS_DeleteLayer(cogr_ds, layer_index)
    GDALClose(cogr_ds)
    if result == OGRERR_UNSUPPORTED_OPERATION:
        raise DatasetDeleteError("Removal of layer {} not supported by driver".format(layer_str))
    elif result != OGRERR_NONE:
        raise DatasetDeleteError("Failed to remove layer {} from datasource: {}".format(layer_str, path))


def _listlayers(path, **kwargs):

    """Provides a list of the layers in an OGR data source.
    """

    cdef void *cogr_ds = NULL
    cdef void *cogr_layer = NULL
    cdef const char *path_c
    cdef const char *name_c

    # Open OGR data source.
    try:
        path_b = path.encode('utf-8')
    except UnicodeDecodeError:
        path_b = path
    path_c = path_b
    cogr_ds = gdal_open_vector(path_c, 0, None, kwargs)

    # Loop over the layers to get their names.
    layer_count = GDALDatasetGetLayerCount(cogr_ds)
    layer_names = []
    for i in range(layer_count):
        cogr_layer = GDALDatasetGetLayer(cogr_ds, i)
        name_c = OGR_L_GetName(cogr_layer)
        name_b = name_c
        layer_names.append(name_b.decode('utf-8'))

    # Close up data source.
    if cogr_ds != NULL:
        GDALClose(cogr_ds)
    cogr_ds = NULL

    return layer_names


def buffer_to_virtual_file(bytesbuf, ext=''):
    """Maps a bytes buffer to a virtual file.

    `ext` is empty or begins with a period and contains at most one period.
    """

    vsi_filename = '/vsimem/{}'.format(uuid.uuid4().hex + ext)
    vsi_cfilename = vsi_filename if not isinstance(vsi_filename, string_types) else vsi_filename.encode('utf-8')

    vsi_handle = VSIFileFromMemBuffer(vsi_cfilename, <unsigned char *>bytesbuf, len(bytesbuf), 0)

    if vsi_handle == NULL:
        raise OSError('failed to map buffer to file')
    if VSIFCloseL(vsi_handle) != 0:
        raise OSError('failed to close mapped file handle')

    return vsi_filename


def remove_virtual_file(vsi_filename):
    vsi_cfilename = vsi_filename if not isinstance(vsi_filename, string_types) else vsi_filename.encode('utf-8')
    return VSIUnlink(vsi_cfilename)


cdef class MemoryFileBase(object):
    """Base for a BytesIO-like class backed by an in-memory file."""

    def __init__(self, file_or_bytes=None, filename=None, ext=''):
        """A file in an in-memory filesystem.

        Parameters
        ----------
        file_or_bytes : file or bytes
            A file opened in binary mode or bytes or a bytearray
        filename : str
            A filename for the in-memory file under /vsimem
        ext : str
            A file extension for the in-memory file under /vsimem. Ignored if
            filename was provided.
        """
        cdef VSILFILE *vsi_handle = NULL

        if file_or_bytes:
            if hasattr(file_or_bytes, 'read'):
                initial_bytes = file_or_bytes.read()
            else:
                initial_bytes = file_or_bytes
            if not isinstance(initial_bytes, (bytearray, bytes)):
                raise TypeError(
                    "Constructor argument must be a file opened in binary "
                    "mode or bytes/bytearray.")
        else:
            initial_bytes = b''

        if filename:
            # GDAL's SRTMHGT driver requires the filename to be "correct" (match
            # the bounds being written)
            self.name = '/vsimem/{0}'.format(filename)
        else:
            # GDAL 2.1 requires a .zip extension for zipped files.
            self.name = '/vsimem/{0}.{1}'.format(uuid.uuid4(), ext.lstrip('.'))

        self.path = self.name.encode('utf-8')
        self._len = 0
        self._pos = 0
        self.closed = False

        self._initial_bytes = initial_bytes
        cdef unsigned char *buffer = self._initial_bytes

        if self._initial_bytes:

            vsi_handle = VSIFileFromMemBuffer(
                self.path, buffer, len(self._initial_bytes), 0)
            self._len = len(self._initial_bytes)

            if vsi_handle == NULL:
                raise IOError(
                    "Failed to create in-memory file using initial bytes.")

            if VSIFCloseL(vsi_handle) != 0:
                raise IOError(
                    "Failed to properly close in-memory file.")

    def exists(self):
        """Test if the in-memory file exists.

        Returns
        -------
        bool
            True if the in-memory file exists.
        """
        cdef VSILFILE *fp = NULL
        cdef const char *cypath = self.path

        with nogil:
            fp = VSIFOpenL(cypath, 'r')

        if fp != NULL:
            VSIFCloseL(fp)
            return True
        else:
            return False

    def __len__(self):
        """Length of the file's buffer in number of bytes.

        Returns
        -------
        int
        """
        cdef unsigned char *buff = NULL
        cdef const char *cfilename = self.path
        cdef vsi_l_offset buff_len = 0
        buff = VSIGetMemFileBuffer(self.path, &buff_len, 0)
        return int(buff_len)

    def close(self):
        """Close MemoryFile and release allocated memory."""
        VSIUnlink(self.path)
        self._pos = 0
        self._initial_bytes = None
        self.closed = True

    def read(self, size=-1):
        """Read size bytes from MemoryFile."""
        cdef VSILFILE *fp = NULL
        # Return no bytes immediately if the position is at or past the
        # end of the file.
        length = len(self)

        if self._pos >= length:
            self._pos = length
            return b''

        if size == -1:
            size = length - self._pos
        else:
            size = min(size, length - self._pos)

        cdef unsigned char *buffer = <unsigned char *>CPLMalloc(size)
        cdef bytes result

        fp = VSIFOpenL(self.path, 'r')

        try:
            fp = exc_wrap_vsilfile(fp)
            if VSIFSeekL(fp, self._pos, 0) < 0:
                raise IOError(
                    "Failed to seek to offset %s in %s.",
                    self._pos, self.name)

            objects_read = VSIFReadL(buffer, 1, size, fp)
            result = <bytes>buffer[:objects_read]

        finally:
            VSIFCloseL(fp)
            CPLFree(buffer)

        self._pos += len(result)
        return result

    def seek(self, offset, whence=0):
        """Seek to position in MemoryFile."""
        if whence == 0:
            pos = offset
        elif whence == 1:
            pos = self._pos + offset
        elif whence == 2:
            pos = len(self) - offset
        if pos < 0:
            raise ValueError("negative seek position: {}".format(pos))
        if pos > len(self):
            raise ValueError("seek position past end of file: {}".format(pos))
        self._pos = pos
        return self._pos

    def tell(self):
        """Tell current position in MemoryFile."""
        return self._pos

    def write(self, data):
        """Write data bytes to MemoryFile"""
        cdef VSILFILE *fp = NULL
        cdef const unsigned char *view = <bytes>data
        n = len(data)

        if not self.exists():
            fp = exc_wrap_vsilfile(VSIFOpenL(self.path, 'w'))
        else:
            fp = exc_wrap_vsilfile(VSIFOpenL(self.path, 'r+'))
            if VSIFSeekL(fp, self._pos, 0) < 0:
                raise IOError(
                    "Failed to seek to offset %s in %s.", self._pos, self.name)

        result = VSIFWriteL(view, 1, n, fp)
        VSIFFlushL(fp)
        VSIFCloseL(fp)

        self._pos += result
        self._len = max(self._len, self._pos)

        return result
