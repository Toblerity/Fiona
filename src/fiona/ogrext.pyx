# These are extension functions and classes using the OGR C API.

import datetime
import locale
import logging
import os
import sys

from six import integer_types, string_types, text_type

from fiona cimport ograpi
from fiona.errors import DriverError, SchemaError, CRSError
from fiona.odict import OrderedDict
from fiona.rfc3339 import parse_date, parse_datetime, parse_time
from fiona.rfc3339 import FionaDateType, FionaDateTimeType, FionaTimeType


log = logging.getLogger("Fiona")
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
log.addHandler(NullHandler())


# Mapping of OGR integer geometry types to GeoJSON type names.
GEOMETRY_TYPES = {
    0: 'Unknown',
    1: 'Point',
    2: 'LineString',
    3: 'Polygon',
    4: 'MultiPoint',
    5: 'MultiLineString',
    6: 'MultiPolygon',
    7: 'GeometryCollection',
    100: 'None',
    101: 'LinearRing',
    0x80000001: '3D Point',
    0x80000002: '3D LineString',
    0x80000003: '3D Polygon',
    0x80000004: '3D MultiPoint',
    0x80000005: '3D MultiLineString',
    0x80000006: '3D MultiPolygon',
    0x80000007: '3D GeometryCollection' }

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
    None,           # OFTBinary, Raw Binary data
    'date',         # OFTDate, Date
    'time',         # OFTTime, Time
    'datetime',     # OFTDateTime, Date and Time
    ]

# Mapping of Fiona field type names to Python types.
FIELD_TYPES_MAP = {
    'int':      int,
    'float':    float,
    'str':      text_type,
    'date':     FionaDateType,
    'time':     FionaTimeType,
    'datetime': FionaDateTimeType
    }

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

# Recent versions of OGR can sometimes detect file encoding, but don't
# provide access yet to the detected encoding. Hence this variable.
OGR_DETECTED_ENCODING = '-ogr-detected-encoding'

# Geometry related functions and classes follow.

cdef void * _createOgrGeomFromWKB(object wkb) except NULL:
    """Make an OGR geometry from a WKB string"""
    geom_type = bytearray(wkb)[1]
    cdef unsigned char *buffer = wkb
    cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(geom_type)
    if cogr_geometry is not NULL:
        ograpi.OGR_G_ImportFromWkb(cogr_geometry, buffer, len(wkb))
    return cogr_geometry

cdef _deleteOgrGeom(void *cogr_geometry):
    """Delete an OGR geometry"""
    if cogr_geometry is not NULL:
        ograpi.OGR_G_DestroyGeometry(cogr_geometry)
    cogr_geometry = NULL


class DimensionsHandler(object):
    """Determines the number of dimensions of a Fiona geometry.
    """
    coordinates = None

    def getNumDimsPoint(self):
        return len(self.coordinates)
    
    def getNumDimsLineString(self):
        return len(self.coordinates[0])
    
    def getNumDimsLinearRing(self):
        return len(self.coordinates[0])
    
    def getNumDimsPolygon(self):
        return len(self.coordinates[0][0])
    
    def getNumDimsMultiPoint(self):
        return len(self.coordinates[0])
    
    def getNumDimsMultiLineString(self):
        return len(self.coordinates[0][0])
    
    def getNumDimsMultiPolygon(self):
        return len(self.coordinates[0][0][0])
    
    def getNumDimsGeometryCollection(self):
        first = self.coordinates[0]
        return self.getNumDims(first['type'], first['coordinates'])
    
    def getNumDims(self, geom_type, coordinates):
        self.coordinates = coordinates
        return getattr(self, 'getNumDims' + geom_type)()


cdef class GeomBuilder:
    """Builds Fiona (GeoJSON) geometries from an OGR geometry handle.
    """
    cdef void *geom
    cdef object code
    cdef object typename
    cdef object ndims

    cdef _buildCoords(self, void *geom):
        # Build a coordinate sequence
        cdef int i
        if geom is NULL:
            raise ValueError("Null geom")
        npoints = ograpi.OGR_G_GetPointCount(geom)
        coords = []
        for i in range(npoints):
            values = [ograpi.OGR_G_GetX(geom, i), ograpi.OGR_G_GetY(geom, i)]
            if self.ndims > 2:
                values.append(ograpi.OGR_G_GetZ(geom, i))
            coords.append(tuple(values))
        return coords
    
    cpdef _buildPoint(self):
        return {'type': 'Point', 'coordinates': self._buildCoords(self.geom)[0]}
    
    cpdef _buildLineString(self):
        return {'type': 'LineString', 'coordinates': self._buildCoords(self.geom)}
    
    cpdef _buildLinearRing(self):
        return {'type': 'LinearRing', 'coordinates': self._buildCoords(self.geom)}
    
    cdef _buildParts(self, void *geom):
        cdef int j
        cdef void *part
        if geom is NULL:
            raise ValueError("Null geom")
        parts = []
        for j in range(ograpi.OGR_G_GetGeometryCount(geom)):
            part = ograpi.OGR_G_GetGeometryRef(geom, j)
            parts.append(GeomBuilder().build(part))
        return parts
    
    cpdef _buildPolygon(self):
        coordinates = [p['coordinates'] for p in self._buildParts(self.geom)]
        return {'type': 'Polygon', 'coordinates': coordinates}
    
    cpdef _buildMultiPoint(self):
        coordinates = [p['coordinates'] for p in self._buildParts(self.geom)]
        return {'type': 'MultiPoint', 'coordinates': coordinates}
    
    cpdef _buildMultiLineString(self):
        coordinates = [p['coordinates'] for p in self._buildParts(self.geom)]
        return {'type': 'MultiLineString', 'coordinates': coordinates}
    
    cpdef _buildMultiPolygon(self):
        coordinates = [p['coordinates'] for p in self._buildParts(self.geom)]
        return {'type': 'MultiPolygon', 'coordinates': coordinates}

    cpdef _buildGeometryCollection(self):
        parts = self._buildParts(self.geom)
        return {'type': 'GeometryCollection', 'geometries': parts}
    
    cdef build(self, void *geom):
        # The only method anyone needs to call
        if geom is NULL:
            raise ValueError("Null geom")
        
        cdef unsigned int etype = ograpi.OGR_G_GetGeometryType(geom)
        self.code = etype
        self.typename = GEOMETRY_TYPES[self.code & (~0x80000000)]
        self.ndims = ograpi.OGR_G_GetCoordinateDimension(geom)
        self.geom = geom
        return getattr(self, '_build' + self.typename)()
    
    cpdef build_wkb(self, object wkb):
        # The only other method anyone needs to call
        cdef object data = wkb
        cdef void *cogr_geometry = _createOgrGeomFromWKB(data)
        result = self.build(cogr_geometry)
        _deleteOgrGeom(cogr_geometry)
        return result


cdef class OGRGeomBuilder:
    """Builds OGR geometries from Fiona geometries.
    """
    cdef object coordinates
    cdef object typename
    cdef object ndims

    cdef void * _buildPoint(self) except NULL:
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(1)
        if cogr_geometry is NULL:
            raise ValueError
        if self.ndims > 2:
            x, y, z = self.coordinates
            ograpi.OGR_G_AddPoint(cogr_geometry, x, y, z)
        else:
            x, y = self.coordinates
            ograpi.OGR_G_AddPoint_2D(cogr_geometry, x, y)
        return cogr_geometry
    
    cdef void * _buildLineString(self) except NULL:
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(2)
        if cogr_geometry is NULL:
            raise ValueError
        for values in self.coordinates:
            log.debug("Adding point %s", values)
            if len(values) > 2:
                x, y, z = values
                ograpi.OGR_G_AddPoint(cogr_geometry, x, y, z)
            else:
                x, y = values
                ograpi.OGR_G_AddPoint_2D(cogr_geometry, x, y)
        return cogr_geometry
    
    cdef void * _buildLinearRing(self) except NULL:
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(101)
        if cogr_geometry is NULL:
            raise ValueError
        for values in self.coordinates:
            log.debug("Adding point %s", values)
            if len(values) > 2:
                x, y, z = values
                ograpi.OGR_G_AddPoint(cogr_geometry, x, y, z)
            else:
                x, y = values
                log.debug("Adding values %f, %f", x, y)
                ograpi.OGR_G_AddPoint_2D(cogr_geometry, x, y)
        log.debug("Closing ring")
        ograpi.OGR_G_CloseRings(cogr_geometry)
        return cogr_geometry
    
    cdef void * _buildPolygon(self) except NULL:
        cdef void *cogr_ring
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(3)
        if cogr_geometry is NULL:
            raise ValueError
        self.ndims = len(self.coordinates[0][0])
        for ring in self.coordinates:
            log.debug("Adding ring %s", ring)
            cogr_ring = OGRGeomBuilder().build(
                {'type': 'LinearRing', 'coordinates': ring} )
            log.debug("Built ring")
            ograpi.OGR_G_AddGeometryDirectly(cogr_geometry, cogr_ring)
            log.debug("Added ring %s", ring)
        return cogr_geometry

    cdef void * _buildMultiPoint(self) except NULL:
        cdef void *cogr_part
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(4)
        if cogr_geometry is NULL:
            raise ValueError
        for values in self.coordinates:
            log.debug("Adding point %s", values)
            cogr_part = ograpi.OGR_G_CreateGeometry(1)
            if len(values) > 2:
                x, y, z = values
                ograpi.OGR_G_AddPoint(cogr_part, x, y, z)
            else:
                x, y = values
                ograpi.OGR_G_AddPoint_2D(cogr_part, x, y)
            ograpi.OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part)
            log.debug("Added point %s", values)
        return cogr_geometry

    cdef void * _buildMultiLineString(self) except NULL:
        cdef void *cogr_part
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(5)
        if cogr_geometry is NULL:
            raise ValueError
        for line in self.coordinates:
            log.debug("Adding line %s", line)
            cogr_part = OGRGeomBuilder().build(
                {'type': 'LineString', 'coordinates': line} )
            log.debug("Built line")
            ograpi.OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part)
            log.debug("Added line %s", line)
        return cogr_geometry

    cdef void * _buildMultiPolygon(self) except NULL:
        cdef void *cogr_part
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(6)
        if cogr_geometry is NULL:
            raise ValueError
        for part in self.coordinates:
            log.debug("Adding polygon %s", part)
            cogr_part = OGRGeomBuilder().build(
                {'type': 'Polygon', 'coordinates': part} )
            log.debug("Built polygon")
            ograpi.OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part)
            log.debug("Added polygon %s", part)
        return cogr_geometry

    cdef void * _buildGeometryCollection(self) except NULL:
        cdef void *cogr_part
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(7)
        if cogr_geometry is NULL:
            raise ValueError
        for part in self.coordinates:
            log.debug("Adding part %s", part)
            cogr_part = OGRGeomBuilder().build(part)
            log.debug("Built part")
            ograpi.OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part)
            log.debug("Added part %s", part)
        return cogr_geometry

    cdef void * build(self, object geometry) except NULL:
        handler = DimensionsHandler()
        self.typename = geometry['type']
        self.coordinates = geometry.get('coordinates')
        if self.coordinates:
            self.ndims = handler.getNumDims(self.typename, self.coordinates)
        if self.typename == 'Point':
            return self._buildPoint()
        elif self.typename == 'LineString':
            return self._buildLineString()
        elif self.typename == 'LinearRing':
            return self._buildLinearRing()
        elif self.typename == 'Polygon':
            return self._buildPolygon()
        elif self.typename == 'MultiPoint':
            return self._buildMultiPoint()
        elif self.typename == 'MultiLineString':
            return self._buildMultiLineString()
        elif self.typename == 'MultiPolygon':
            return self._buildMultiPolygon()
        elif self.typename == 'GeometryCollection':
            self.coordinates = geometry.get('geometries')
            self.ndims = handler.getNumDims(self.typename, self.coordinates)
            return self._buildGeometryCollection()
        else:
            raise ValueError("Unsupported geometry type %s" % self.typename)


cdef geometry(void *geom):
    """Factory for Fiona geometries"""
    return GeomBuilder().build(geom)


def geometryRT(geometry):
    # For testing purposes only, leaks the JSON data
    cdef void *cogr_geometry = OGRGeomBuilder().build(geometry)
    log.debug("Geometry: %s" % ograpi.OGR_G_ExportToJson(cogr_geometry))
    result = GeomBuilder().build(cogr_geometry)
    _deleteOgrGeom(cogr_geometry)
    return result


# Feature extension classes and functions follow.

cdef class FeatureBuilder:
    """Build Fiona features from OGR feature pointers.

    No OGR objects are allocated by this function and the feature
    argument is not destroyed.
    """

    cdef build(self, void *feature, encoding='utf-8'):
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
        cdef int retval
        cdef char *key_c
        props = OrderedDict()
        for i in range(ograpi.OGR_F_GetFieldCount(feature)):
            fdefn = ograpi.OGR_F_GetFieldDefnRef(feature, i)
            if fdefn is NULL:
                raise ValueError("Null feature definition")
            key_c = ograpi.OGR_Fld_GetNameRef(fdefn)
            if key_c == NULL:
                raise ValueError("Null field name reference")
            key_b = key_c
            key = key_b.decode('utf-8')
            fieldtypename = FIELD_TYPES[ograpi.OGR_Fld_GetType(fdefn)]
            if not fieldtypename:
                log.warn(
                    "Skipping field %s: invalid type %s", 
                    key,
                    ograpi.OGR_Fld_GetType(fdefn))
                continue
            # TODO: other types
            fieldtype = FIELD_TYPES_MAP[fieldtypename]
            if not ograpi.OGR_F_IsFieldSet(feature, i):
                props[key] = None
            elif fieldtype is int:
                props[key] = ograpi.OGR_F_GetFieldAsInteger(feature, i)
            elif fieldtype is float:
                props[key] = ograpi.OGR_F_GetFieldAsDouble(feature, i)
            elif fieldtype is text_type:
                try:
                    val = ograpi.OGR_F_GetFieldAsString(feature, i)
                    props[key] = val.decode(encoding)
                except UnicodeDecodeError:
                    log.warn(
                        "Failed to decode %s using %s codec", val, encoding)
                    props[key] = val
            elif fieldtype in (FionaDateType, FionaTimeType, FionaDateTimeType):
                retval = ograpi.OGR_F_GetFieldAsDateTime(
                    feature, i, &y, &m, &d, &hh, &mm, &ss, &tz)
                if fieldtype is FionaDateType:
                    props[key] = datetime.date(y, m, d).isoformat()
                elif fieldtype is FionaTimeType:
                    props[key] = datetime.time(hh, mm, ss).isoformat()
                else:
                    props[key] = datetime.datetime(
                        y, m, d, hh, mm, ss).isoformat()
            else:
                log.debug("%s: None, fieldtype: %r, %r" % (key, fieldtype, fieldtype in string_types))
                props[key] = None

        cdef void *cogr_geometry = ograpi.OGR_F_GetGeometryRef(feature)
        if cogr_geometry is not NULL:
            geom = GeomBuilder().build(cogr_geometry)
        else:
            geom = None
        return {
            'type': 'Feature',
            'id': str(ograpi.OGR_F_GetFID(feature)),
            'geometry': geom,
            'properties': props }


cdef class OGRFeatureBuilder:
    
    """Builds an OGR Feature from a Fiona feature mapping.

    Allocates one OGR Feature which should be destroyed by the caller.
    Borrows a layer definition from the collection.
    """
    
    cdef void * build(self, feature, collection) except NULL:
        cdef char *string_c
        cdef WritingSession session
        session = collection.session
        cdef void *cogr_layer = session.cogr_layer
        if cogr_layer is NULL:
            raise ValueError("Null layer")
        cdef void *cogr_featuredefn = ograpi.OGR_L_GetLayerDefn(cogr_layer)
        if cogr_featuredefn is NULL:
            raise ValueError("Null feature definition")
        cdef void *cogr_feature = ograpi.OGR_F_Create(cogr_featuredefn)
        if cogr_feature is NULL:
            raise ValueError("Null feature")
        
        cdef void *cogr_geometry = OGRGeomBuilder().build(feature['geometry'])
        ograpi.OGR_F_SetGeometryDirectly(cogr_feature, cogr_geometry)
        
        # OGR_F_SetFieldString takes UTF-8 encoded strings ('bytes' in 
        # Python 3).
        encoding = session.get_internalencoding()

        for key, value in feature['properties'].items():
            try:
                key_bytes = key.encode(encoding)
            except UnicodeDecodeError:
                log.warn("Failed to encode %s using %s codec", key, encoding)
                key_bytes = key
            key_c = key_bytes
            i = ograpi.OGR_F_GetFieldIndex(cogr_feature, key_c)
            if i < 0:
                continue
            if isinstance(value, integer_types):
                ograpi.OGR_F_SetFieldInteger(cogr_feature, i, value)
            elif isinstance(value, float):
                ograpi.OGR_F_SetFieldDouble(cogr_feature, i, value)
            elif isinstance(value, string_types):
                try:
                    value_bytes = value.encode(encoding)
                except UnicodeDecodeError:
                    log.warn(
                        "Failed to encode %s using %s codec", value, encoding)
                    value_bytes = value
                string_c = value_bytes
                ograpi.OGR_F_SetFieldString(cogr_feature, i, string_c)
            elif isinstance(value, (FionaDateType, FionaTimeType, FionaDateTimeType)):
                if isinstance(value, FionaDateType):
                    y, m, d, hh, mm, ss, ff = parse_date(value)
                elif isinstance(value, FionaTimeType):
                    y, m, d, hh, mm, ss, ff = parse_time(value)
                else:
                    y, m, d, hh, mm, ss, ff = parse_datetime(value)
                ograpi.OGR_F_SetFieldDateTime(
                    cogr_feature, i, y, m, d, hh, mm, ss, 0)
            elif value is None:
                pass # keep field unset/null
            else:
                raise ValueError("Invalid field type %s" % type(value))
            log.debug("Set field %s: %s" % (key, value))
        return cogr_feature


cdef _deleteOgrFeature(void *cogr_feature):
    """Delete an OGR feature"""
    if cogr_feature is not NULL:
        ograpi.OGR_F_Destroy(cogr_feature)
    cogr_feature = NULL


def featureRT(feature, collection):
    # For testing purposes only, leaks the JSON data
    cdef void *cogr_feature = OGRFeatureBuilder().build(feature, collection)
    cdef void *cogr_geometry = ograpi.OGR_F_GetGeometryRef(cogr_feature)
    if cogr_geometry is NULL:
        raise ValueError("Null geometry")
    log.debug("Geometry: %s" % ograpi.OGR_G_ExportToJson(cogr_geometry))
    encoding = collection.encoding or 'utf-8'
    result = FeatureBuilder().build(cogr_feature, encoding)
    _deleteOgrFeature(cogr_feature)
    return result


# Collection-related extension classes and functions

cdef class Session:
    
    cdef void *cogr_ds
    cdef void *cogr_layer
    cdef object _fileencoding
    cdef object _encoding
    cdef object collection

    def __cinit__(self):
        self.cogr_ds = NULL
        self.cogr_layer = NULL
        self._fileencoding = None
        self._encoding = None

    def __dealloc__(self):
        self.stop()

    def start(self, collection):
        cdef char *path_c
        cdef char *name_c
        
        try:
            path_b = collection.path.encode('utf-8')
        except UnicodeDecodeError:
            # Presume already a UTF-8 encoded string
            path_b = collection.path
        path_c = path_b
        
        self.cogr_ds = ograpi.OGROpen(path_c, 0, NULL)
        if self.cogr_ds is NULL:
            raise ValueError(
                "No data available at path '%s'" % collection.path)
        
        if isinstance(collection.name, string_types):
            name_b = collection.name.encode('utf-8')
            name_c = name_b
            self.cogr_layer = ograpi.OGR_DS_GetLayerByName(
                                self.cogr_ds, name_c)
        elif isinstance(collection.name, int):
            self.cogr_layer = ograpi.OGR_DS_GetLayer(
                                self.cogr_ds, collection.name)
            name_c = ograpi.OGR_L_GetName(self.cogr_layer)
            name_b = name_c
            collection.name = name_b.decode('utf-8')

        if self.cogr_layer is NULL:
            raise ValueError("Null layer: " + repr(collection.name))
        
        self.collection = collection
        
        userencoding = self.collection.encoding
        if userencoding:
            ograpi.CPLSetThreadLocalConfigOption('SHAPE_ENCODING', '')
            self._fileencoding = userencoding.upper()
        else:
            self._fileencoding = (
                ograpi.OGR_L_TestCapability(
                    self.cogr_layer, "StringsAsUTF8") and
                OGR_DETECTED_ENCODING) or (
                self.get_driver() == "ESRI Shapefile" and
                'ISO-8859-1') or locale.getpreferredencoding().upper()

    def stop(self):
        self.cogr_layer = NULL
        if self.cogr_ds is not NULL:
            ograpi.OGR_DS_Destroy(self.cogr_ds)
        self.cogr_ds = NULL

    def get_fileencoding(self):
        return self._fileencoding

    def get_internalencoding(self):
        if not self._encoding:
            fileencoding = self.get_fileencoding()
            self._encoding = (
                ograpi.OGR_L_TestCapability(
                    self.cogr_layer, "StringsAsUTF8") and
                'utf-8') or fileencoding
        return self._encoding

    def get_length(self):
        if self.cogr_layer is NULL:
            raise ValueError("Null layer")
        return ograpi.OGR_L_GetFeatureCount(self.cogr_layer, 0)

    def get_driver(self):
        cdef void *cogr_driver = ograpi.OGR_DS_GetDriver(self.cogr_ds)
        if cogr_driver is NULL:
            raise ValueError("Null driver")
        cdef char *name = ograpi.OGR_Dr_GetName(cogr_driver)
        driver_name = name
        return driver_name.decode()
 
    def get_schema(self):
        cdef int i
        cdef int n
        cdef void *cogr_featuredefn
        cdef void *cogr_fielddefn
        cdef char *key_c
        props = []
        
        if self.cogr_layer is NULL:
            raise ValueError("Null layer")

        cogr_featuredefn = ograpi.OGR_L_GetLayerDefn(self.cogr_layer)
        if cogr_featuredefn is NULL:
            raise ValueError("Null feature definition")
        n = ograpi.OGR_FD_GetFieldCount(cogr_featuredefn)
        for i from 0 <= i < n:
            cogr_fielddefn = ograpi.OGR_FD_GetFieldDefn(cogr_featuredefn, i)
            if cogr_fielddefn is NULL:
                raise ValueError("Null field definition")
            key_c = ograpi.OGR_Fld_GetNameRef(cogr_fielddefn)
            key_b = key_c
            if not bool(key_b):
                raise ValueError("Invalid field name ref: %s" % key)
            key = key_b.decode('utf-8')
            fieldtypename = FIELD_TYPES[ograpi.OGR_Fld_GetType(cogr_fielddefn)]
            if not fieldtypename:
                log.warn(
                    "Skipping field %s: invalid type %s", 
                    key,
                    ograpi.OGR_Fld_GetType(cogr_fielddefn))
                continue
            val = fieldtypename
            if fieldtypename == 'float':
                fmt = ""
                width = ograpi.OGR_Fld_GetWidth(cogr_fielddefn)
                if width and width != 24:
                    fmt = ":%d" % width
                precision = ograpi.OGR_Fld_GetPrecision(cogr_fielddefn)
                if precision and precision != 15:
                    fmt += ".%d" % precision
                val = "float" + fmt
            elif fieldtypename == 'int':
                fmt = ""
                width = ograpi.OGR_Fld_GetWidth(cogr_fielddefn)
                if width and width != 11:
                    fmt = ":%d" % width
                val = fieldtypename + fmt
            elif fieldtypename == 'str':
                fmt = ""
                width = ograpi.OGR_Fld_GetWidth(cogr_fielddefn)
                if width and width != 80:
                    fmt = ":%d" % width
                val = fieldtypename + fmt

            props.append((key, val))

        cdef unsigned int geom_type = ograpi.OGR_FD_GetGeomType(
            cogr_featuredefn)
        return {
            'properties': OrderedDict(props), 
            'geometry': GEOMETRY_TYPES[geom_type]}

    def get_crs(self):
        cdef char *proj_c = NULL
        if self.cogr_layer is NULL:
            raise ValueError("Null layer")
        cdef void *cogr_crs = ograpi.OGR_L_GetSpatialRef(self.cogr_layer)
        log.debug("Got coordinate system")
        crs = {}
        if cogr_crs is not NULL:
            ograpi.OSRExportToProj4(cogr_crs, &proj_c)
            if proj_c is NULL:
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
            ograpi.CPLFree(proj_c)
        else:
            log.debug("Projection not found (cogr_crs was NULL)")
        return crs

    def get_extent(self):
        if self.cogr_layer is NULL:
            raise ValueError("Null layer")
        cdef ograpi.OGREnvelope extent
        result = ograpi.OGR_L_GetExtent(self.cogr_layer, &extent, 1)
        return (extent.MinX, extent.MinY, extent.MaxX, extent.MaxY)

    def isactive(self):
        if self.cogr_layer != NULL and self.cogr_ds != NULL:
            return 1
        else:
            return 0


cdef class WritingSession(Session):
    
    def start(self, collection):
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
                self.cogr_ds = ograpi.OGROpen(path_c, 1, NULL)
                if self.cogr_ds is NULL:
                    raise RuntimeError("Failed to open %s" % path)
                cogr_driver = ograpi.OGR_DS_GetDriver(self.cogr_ds)
                if cogr_driver is NULL:
                    raise ValueError("Null driver")

                if isinstance(collection.name, string_types):
                    name_b = collection.name.encode()
                    name_c = name_b
                    self.cogr_layer = ograpi.OGR_DS_GetLayerByName(
                                        self.cogr_ds, name_c)
                elif isinstance(collection.name, int):
                    self.cogr_layer = ograpi.OGR_DS_GetLayer(
                                        self.cogr_ds, collection.name)

                if self.cogr_layer is NULL:
                    raise RuntimeError(
                        "Failed to get layer %s" % collection.name)
            else:
                raise OSError("No such file or directory %s" % path)

            userencoding = self.collection.encoding
            self._fileencoding = (userencoding or (
                ograpi.OGR_L_TestCapability(self.cogr_layer, "StringsAsUTF8") and
                OGR_DETECTED_ENCODING) or (
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

            cogr_driver = ograpi.OGRGetDriverByName(driver_c)
            if cogr_driver is NULL:
                raise ValueError("Null driver")

            if not os.path.exists(path):
                cogr_ds = ograpi.OGR_Dr_CreateDataSource(
                    cogr_driver, path_c, NULL)

            else:
                cogr_ds = ograpi.OGROpen(path_c, 1, NULL)
                
                if not cogr_ds:
                    cogr_ds = ograpi.OGR_Dr_CreateDataSource(
                        cogr_driver, path_c, NULL)

                elif collection.name is None:
                    ograpi.OGR_DS_Destroy(cogr_ds)
                    cogr_ds == NULL
                    log.debug("Deleted pre-existing data at %s", path)
                    
                    cogr_ds = ograpi.OGR_Dr_CreateDataSource(
                        cogr_driver, path_c, NULL)

                else:
                    pass

            if cogr_ds is NULL:
                raise RuntimeError("Failed to open %s" % path)
            else:
                self.cogr_ds = cogr_ds

            # Set the spatial reference system from the given crs.
            if collection.crs:
                cogr_srs = ograpi.OSRNewSpatialReference(NULL)
                if cogr_srs is NULL:
                    raise ValueError("Null spatial reference")
                params = []
                for k, v in collection.crs.items():
                    if v is True or (k == 'no_defs' and v):
                        params.append("+%s" % k)
                    else:
                        params.append("+%s=%s" % (k, v))
                proj = " ".join(params)
                proj_b = proj.encode()
                proj_c = proj_b
                ograpi.OSRImportFromProj4(cogr_srs, proj_c)

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
                options = ograpi.CSLSetNameValue(options, "ENCODING", fileencoding_c)

            # Does the layer exist already? If so, we delete it.
            layer_count = ograpi.OGR_DS_GetLayerCount(self.cogr_ds)
            layer_names = []
            for i in range(layer_count):
                cogr_layer = ograpi.OGR_DS_GetLayer(cogr_ds, i)
                name_c = ograpi.OGR_L_GetName(cogr_layer)
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
                ograpi.OGR_DS_DeleteLayer(self.cogr_ds, idx)
            
            # Create the named layer in the datasource.
            name_b = collection.name.encode('utf-8')
            name_c = name_b
            self.cogr_layer = ograpi.OGR_DS_CreateLayer(
                self.cogr_ds, 
                name_c,
                cogr_srs,
                <unsigned int>[k for k,v in GEOMETRY_TYPES.items() if 
                    v == collection.schema.get('geometry', 'Unknown')][0],
                options
                )
            if options:
                ograpi.CSLDestroy(options)

            if self.cogr_layer is NULL:
                raise ValueError("Null layer")
            log.debug("Created layer")
            
            # Next, make a layer definition from the given schema properties,
            # which are an ordered dict since Fiona 1.0.1.
            for key, value in collection.schema['properties'].items():
                log.debug("Creating field: %s %s", key, value)
                
                # Is there a field width/precision?
                width = precision = None
                if ':' in value:
                    value, fmt = value.split(':')
                    if '.' in fmt:
                        width, precision = map(int, fmt.split('.'))
                    else:
                        width = int(fmt)
                
                encoding = self.get_internalencoding()
                key_bytes = key.encode(encoding)
                cogr_fielddefn = ograpi.OGR_Fld_Create(
                    key_bytes, 
                    FIELD_TYPES.index(value) )
                if cogr_fielddefn is NULL:
                    raise ValueError("Null field definition")
                if width:
                    ograpi.OGR_Fld_SetWidth(cogr_fielddefn, width)
                if precision:
                    ograpi.OGR_Fld_SetPrecision(cogr_fielddefn, precision)
                ograpi.OGR_L_CreateField(self.cogr_layer, cogr_fielddefn, 1)
                ograpi.OGR_Fld_Destroy(cogr_fielddefn)
            log.debug("Created fields")

        log.debug("Writing started")

    def writerecs(self, records, collection):
        """Writes buffered records to OGR."""
        cdef void *cogr_driver
        cdef void *cogr_feature

        cdef void *cogr_layer = self.cogr_layer
        if cogr_layer is NULL:
            raise ValueError("Null layer")
        
        schema_geom_type = collection.schema['geometry']
        cogr_driver = ograpi.OGR_DS_GetDriver(self.cogr_ds)
        if ograpi.OGR_Dr_GetName(cogr_driver) == b"GeoJSON":
            def validate_geometry_type(rec):
                return True
        elif ograpi.OGR_Dr_GetName(cogr_driver) == b"ESRI Shapefile" \
                and "Point" not in collection.schema['geometry']:
            schema_geom_type = collection.schema['geometry'].lstrip(
                "3D ").lstrip("Multi")
            def validate_geometry_type(rec):
                return rec['geometry']['type'].lstrip(
                    "Multi") == schema_geom_type
        else:
            schema_geom_type = collection.schema['geometry'].lstrip("3D ")
            def validate_geometry_type(rec):
                return rec['geometry']['type'] == schema_geom_type

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
            result = ograpi.OGR_L_CreateFeature(cogr_layer, cogr_feature)
            if result != OGRERR_NONE:
                raise RuntimeError("Failed to write record: %s" % record)
            _deleteOgrFeature(cogr_feature)

    def sync(self, collection):
        """Syncs OGR to disk."""
        cdef void *cogr_ds = self.cogr_ds
        cdef void *cogr_layer = self.cogr_layer
        if cogr_ds is NULL:
            raise ValueError("Null data source")
        log.debug("Syncing OGR to disk")
        retval = ograpi.OGR_DS_SyncToDisk(cogr_ds)
        if retval != OGRERR_NONE:
            raise RuntimeError("Failed to sync to disk")


cdef class Iterator:

    """Provides iterated access to feature data.
    """

    # Reference to its Collection
    cdef collection
    cdef encoding

    def __init__(self, collection, bbox=None):
        if collection.session is None:
            raise ValueError("I/O operation on closed collection")
        self.collection = collection
        cdef Session session
        session = self.collection.session
        cdef void *cogr_layer = session.cogr_layer
        if cogr_layer is NULL:
            raise ValueError("Null layer")
        ograpi.OGR_L_ResetReading(cogr_layer)
        if bbox:
            ograpi.OGR_L_SetSpatialFilterRect(
                cogr_layer, bbox[0], bbox[1], bbox[2], bbox[3])
        self.encoding = session.get_internalencoding()

    def __iter__(self):
        return self

    def __next__(self):
        cdef long fid
        cdef void * cogr_feature
        cdef Session session
        session = self.collection.session
        cogr_feature = ograpi.OGR_L_GetNextFeature(session.cogr_layer)
        if cogr_feature == NULL:
            raise StopIteration
        feature = FeatureBuilder().build(cogr_feature, self.encoding)
        _deleteOgrFeature(cogr_feature)
        return feature


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
    cogr_ds = ograpi.OGROpen(path_c, 0, NULL)
    if cogr_ds is NULL:
        raise ValueError("No data available at path '%s'" % path)
    
    # Loop over the layers to get their names.
    layer_count = ograpi.OGR_DS_GetLayerCount(cogr_ds)
    layer_names = []
    for i in range(layer_count):
        cogr_layer = ograpi.OGR_DS_GetLayer(cogr_ds, i)
        name_c = ograpi.OGR_L_GetName(cogr_layer)
        name_b = name_c
        layer_names.append(name_b.decode('utf-8'))
    
    # Close up data source.
    if cogr_ds is not NULL:
        ograpi.OGR_DS_Destroy(cogr_ds)
    cogr_ds = NULL

    return layer_names

