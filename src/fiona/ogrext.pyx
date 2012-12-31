# These are extension functions and classes using the OGR C API.

import datetime
import logging
import os
import sys
from types import IntType, FloatType, StringType, UnicodeType

from fiona cimport ograpi
from fiona import ogrinit
from fiona.rfc3339 import parse_date, parse_datetime, parse_time

log = logging.getLogger("Fiona")

# Mapping of OGR integer geometry types to GeoJSON type names.
GEOMETRY_TYPES = [
    'Unknown', 'Point', 'LineString', 'Polygon', 'MultiPoint', 
    'MultiLineString', 'MultiPolygon', 'GeometryCollection' ]

# Mapping of OGR integer field types to Fiona field type names.
#
# Lists are currently unsupported in this version, but might be done as
# arrays in a future version.
#
# Fiona tries to conform to RFC 3339 with respect to date and time. Its
# 'date', 'time', and 'datetime' types are sub types of 'str'.
#

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

class FionaDateType(UnicodeType):
    pass

class FionaTimeType(UnicodeType):
    pass

class FionaDateTimeType(UnicodeType):
    pass

# Mapping of Fiona field type names to Python types.
FIELD_TYPES_MAP = {
    'int':      IntType,
    'float':    FloatType,
    'str':      UnicodeType,
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
        self.code = ograpi.OGR_G_GetGeometryType(geom)
        self.typename = GEOMETRY_TYPES[self.code % 0x80000000]
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

    cdef build(self, void *feature):
        # The only method anyone ever needs to call
        if feature is NULL:
            raise ValueError("Null feature")
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
        props = {}
        for i in range(ograpi.OGR_F_GetFieldCount(feature)):
            fdefn = ograpi.OGR_F_GetFieldDefnRef(feature, i)
            if fdefn is NULL:
                raise ValueError("Null feature definition")
            key = ograpi.OGR_Fld_GetNameRef(fdefn)
            if key is NULL:
                raise ValueError("Null field name reference")
            fieldtypename = FIELD_TYPES[ograpi.OGR_Fld_GetType(fdefn)]
            if not fieldtypename:
                raise ValueError(
                    "Invalid field type %s" % ograpi.OGR_Fld_GetType(fdefn))
            # TODO: other types
            fieldtype = FIELD_TYPES_MAP[fieldtypename]
            if not ograpi.OGR_F_IsFieldSet(feature, i):
                props[key] = None
            elif fieldtype is IntType:
                props[key] = ograpi.OGR_F_GetFieldAsInteger(feature, i)
            elif fieldtype is FloatType:
                props[key] = ograpi.OGR_F_GetFieldAsDouble(feature, i)
            elif fieldtype is UnicodeType:
                try:
                    val = ograpi.OGR_F_GetFieldAsString(feature, i)
                    props[key] = val.decode('utf-8')
                except UnicodeDecodeError:
                    log.warn("Failed to decode %s using UTF-8 codec", val)
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
                props[key] = None

        cdef void *cogr_geometry = ograpi.OGR_F_GetGeometryRef(feature)
        if cogr_geometry is NULL:
            raise ValueError("Null geometry")
        geom = GeomBuilder().build(cogr_geometry)
        
        return {
            'id': str(ograpi.OGR_F_GetFID(feature)),
            'geometry': geom,
            'properties': props }


cdef class OGRFeatureBuilder:
    
    """Builds an OGR Feature from a Fiona feature mapping.

    Allocates one OGR Feature which should be destroyed by the caller.
    Borrows a layer definition from the collection.
    """
    
    cdef void * build(self, feature, collection) except NULL:
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
        
        for key, value in feature['properties'].items():
            try:
                key_encoded = key.encode('utf-8')
            except UnicodeDecodeError:
                log.warn("Failed to encode %s using UTF-8 codec", key)
                key_encoded = key
            i = ograpi.OGR_F_GetFieldIndex(cogr_feature, key_encoded)
            ptype = type(value) #FIELD_TYPES_MAP[key]
            if ptype is IntType:
                ograpi.OGR_F_SetFieldInteger(cogr_feature, i, value)
            elif ptype is FloatType:
                ograpi.OGR_F_SetFieldDouble(cogr_feature, i, value)
            elif ptype in (UnicodeType, StringType):
                try:
                    value_encoded = value.encode('utf-8')
                except UnicodeDecodeError:
                    log.warn("Failed to encode %s using UTF-8 codec", value)
                    value_encoded = value
                ograpi.OGR_F_SetFieldString(cogr_feature, i, value_encoded)
            elif ptype in (FionaDateType, FionaTimeType, FionaDateTimeType):
                if ptype is FionaDateType:
                    y, m, d, hh, mm, ss, ff = parse_date(value)
                elif ptype is FionaTimeType:
                    y, m, d, hh, mm, ss, ff = parse_time(value)
                else:
                    y, m, d, hh, mm, ss, ff = parse_datetime(value)
                ograpi.OGR_F_SetFieldDateTime(
                    cogr_feature, i, y, m, d, hh, mm, ss, 0)
            elif value is None:
                pass # keep field unset/null
            else:
                raise ValueError("Invalid field type %s" % ptype)
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
    result = FeatureBuilder().build(cogr_feature)
    _deleteOgrFeature(cogr_feature)
    return result


# Collection-related extension classes and functions

cdef class Session:
    
    cdef void *cogr_ds
    cdef void *cogr_layer

    def __cinit__(self):
        self.cogr_ds = NULL
        self.cogr_layer = NULL

    def __dealloc__(self):
        self.stop()

    def start(self, collection):
        self.cogr_ds = ograpi.OGROpen(collection.path, 0, NULL)
        if self.cogr_ds is NULL:
            raise ValueError("Null data source")
        self.cogr_layer = ograpi.OGR_DS_GetLayerByName(
            self.cogr_ds, collection.name)
        if self.cogr_layer is NULL:
            raise ValueError("Null layer")

    def stop(self):
        self.cogr_layer = NULL
        if self.cogr_ds is not NULL:
            ograpi.OGR_DS_Destroy(self.cogr_ds)
        self.cogr_ds = NULL

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
        return driver_name
 
    def get_schema(self):
        cdef int i
        cdef int n
        cdef void *cogr_featuredefn
        cdef void *cogr_fielddefn
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
            fieldtypename = FIELD_TYPES[ograpi.OGR_Fld_GetType(cogr_fielddefn)]
            if not fieldtypename:
                raise ValueError(
                    "Invalid field type %s" % ograpi.OGR_Fld_GetType(
                                                cogr_fielddefn))
            key = ograpi.OGR_Fld_GetNameRef(cogr_fielddefn)
            if not bool(key):
                raise ValueError("Invalid field name ref: %s" % key)
            try:
                key = key.decode('utf-8')
            except UnicodeDecodeError:
                log.warn("Failed to decode %s using UTF-8 codec", key)
            props.append((key, fieldtypename))
        geom_type = ograpi.OGR_FD_GetGeomType(cogr_featuredefn)
        return {'properties': dict(props), 'geometry': GEOMETRY_TYPES[geom_type]}

    def get_crs(self):
        cdef char *proj = NULL
        if self.cogr_layer is NULL:
            raise ValueError("Null layer")
        cdef void *cogr_crs = ograpi.OGR_L_GetSpatialRef(self.cogr_layer)
        log.debug("Got coordinate system")
        crs = {}
        if cogr_crs is not NULL:
            ograpi.OSRExportToProj4(cogr_crs, &proj)
            if proj is NULL:
                raise ValueError("Null projection")
            log.debug("Params: %s", proj)
            value = proj
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
            ograpi.CPLFree(proj)
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
        cdef void *cogr_srs = NULL
        path = collection.path

        if collection.mode == 'a':
            if os.path.exists(path):
                self.cogr_ds = ograpi.OGROpen(path, 1, NULL)
                if self.cogr_ds is NULL:
                    raise RuntimeError("Failed to open %s" % path)
                cogr_driver = ograpi.OGR_DS_GetDriver(self.cogr_ds)
                if cogr_driver is NULL:
                    raise ValueError("Null driver")
                self.cogr_layer = ograpi.OGR_DS_GetLayerByName(
                                        self.cogr_ds, collection.name)
                if self.cogr_layer is NULL:
                    raise RuntimeError(
                        "Failed to get layer %s" % collection.name)
            else:
                raise OSError("No such file or directory %s" % path)

        elif collection.mode == 'w':
            if os.path.exists(path):
                self.cogr_ds = ograpi.OGROpen(path, 1, NULL)
                if self.cogr_ds is not NULL:
                    cogr_driver = ograpi.OGR_DS_GetDriver(self.cogr_ds)
                    if cogr_driver is NULL:
                        raise ValueError("Null driver")
                    ograpi.OGR_DS_Destroy(self.cogr_ds)
                    ograpi.OGR_Dr_DeleteDataSource(cogr_driver, path)
                    log.debug("Deleted pre-existing data at %s", path)
            cogr_driver = ograpi.OGRGetDriverByName(collection.driver)
            if cogr_driver is NULL:
                raise ValueError("Null driver")
            self.cogr_ds = ograpi.OGR_Dr_CreateDataSource(
                cogr_driver, path, NULL)
            if self.cogr_ds is NULL:
                raise RuntimeError("Failed to open %s" % path)

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
                ograpi.OSRImportFromProj4(cogr_srs, <char *>proj)

            self.cogr_layer = ograpi.OGR_DS_CreateLayer(
                self.cogr_ds, 
                collection.name,
                cogr_srs,
                GEOMETRY_TYPES.index(collection.schema['geometry']),
                NULL
                )
            if self.cogr_layer is NULL:
                raise ValueError("Null layer")
            log.debug("Created layer")
            
            # Next, make a layer definition from the given schema.
            for key, value in collection.schema['properties'].items():
                log.debug("Creating field: %s %s", key, value)
                # OGR needs UTF-8 field names.
                key_encoded = key.encode("utf-8")
                cogr_fielddefn = ograpi.OGR_Fld_Create(
                    key_encoded, 
                    FIELD_TYPES.index(value) )
                if cogr_fielddefn is NULL:
                    raise ValueError("Null field definition")
                ograpi.OGR_L_CreateField(self.cogr_layer, cogr_fielddefn, 1)
                ograpi.OGR_Fld_Destroy(cogr_fielddefn)
            log.debug("Created fields")

        log.debug("Writing started")

    def writerecs(self, records, collection):
        """Writes buffered records to OGR."""
        
        cdef void *cogr_layer = self.cogr_layer
        if cogr_layer is NULL:
            raise ValueError("Null layer")
        cdef void *cogr_feature

        for record in records:
            log.debug("Creating feature in layer: %s" % record)
            # Validate against collection's schema.
            if (
                    set(record['properties'].keys()) -
                    set(collection.schema['properties'].keys())
                    ) or (
                        record['geometry']['type'] != \
                        collection.schema['geometry'] ):
                raise ValueError(
                    "Record (%s) not match collection schema (%s)" % (
                        {'properties': record['properties'].keys(),
                         'geometry': record['geometry']['type']},
                        {'properties': collection.schema['properties'].keys(),
                         'geometry': collection.schema['geometry']}, ))

            cogr_feature = OGRFeatureBuilder().build(record, collection)
            result = ograpi.OGR_L_CreateFeature(cogr_layer, cogr_feature)
            if result != OGRERR_NONE:
                raise RuntimeError("Failed to write record: %s" % record)
            _deleteOgrFeature(cogr_feature)

    def sync(self):
        """Syncs OGR to disk."""
        cdef void *cogr_ds = self.cogr_ds
        if cogr_ds is NULL:
            raise ValueError("Null data source")
        log.debug("Syncing OGR to disk")
        result = ograpi.OGR_DS_SyncToDisk(cogr_ds)
        if result != OGRERR_NONE:
            raise RuntimeError("Failed to sync to disk")


cdef class Iterator:

    """Provides iterated access to feature data.
    """

    # Reference to its Collection
    cdef collection

    def __init__(self, collection, bbox=None):
        if collection.session is None:
            raise ValueError("I/O operation on closed collection")
        self.collection = collection
        cdef Session session
        session = self.collection.session
        cdef void *cogr_layer = session.cogr_layer
        if cogr_layer is NULL:
            raise ValueError("Null layer")
        if bbox:
            ograpi.OGR_L_SetSpatialFilterRect(
                cogr_layer, bbox[0], bbox[1], bbox[2], bbox[3])

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
        feature = FeatureBuilder().build(cogr_feature)
        _deleteOgrFeature(cogr_feature)
        return feature

