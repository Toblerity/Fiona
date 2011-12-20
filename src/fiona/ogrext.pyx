# These are extension functions and classes using the OGR C API.

import logging
import os
import sys
from types import IntType, FloatType, StringType, UnicodeType

from fiona cimport ograpi
from fiona import ogrinit

log = logging.getLogger("Fiona")

# Mapping of OGR integer geometry types to GeoJSON type names.
GEOMETRY_TYPES = [
    'Unknown', 'Point', 'LineString', 'Polygon', 'MultiPoint', 
    'MultiLineString', 'MultiPolygon', 'GeometryCollection' ]

# Mapping of OGR integer field types to Fiona field type names.
#
# Only ints, floats, and unicode strings are supported. On the web, dates and
# times are represented as strings (see RFC 3339). 
FIELD_TYPES = [
    'int',          # OFTInteger, Simple 32bit integer
    None,           # OFTIntegerList, List of 32bit integers
    'float',       # OFTReal, Double Precision floating point
    None,           # OFTRealList, List of doubles
    'str',          # OFTString, String of ASCII chars
    None,           # OFTStringList, Array of strings
    None,           # OFTWideString, deprecated
    None,           # OFTWideStringList, deprecated
    None,           # OFTBinary, Raw Binary data
    None,           # OFTDate, Date
    None,           # OFTTime, Time
    None,           # OFTDateTime, Date and Time
    ]

# Mapping of Fiona field type names to Python types.
FIELD_TYPES_MAP = {
    'int':      IntType,
    'float':    FloatType,
    'str':      UnicodeType,
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

cdef void * _createOgrGeomFromWKB(object wkb):
    """Make an OGR geometry from a WKB string"""
    geom_type = bytearray(wkb)[1]
    cdef unsigned char *buffer = wkb
    cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(geom_type)
    ograpi.OGR_G_ImportFromWkb(cogr_geometry, buffer, len(wkb))
    return cogr_geometry


cdef _deleteOgrGeom(void *cogr_geometry):
    """Delete an OGR geometry"""
    if cogr_geometry != NULL:
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
        self.code = ograpi.OGR_G_GetGeometryType(geom)
        self.typename = GEOMETRY_TYPES[self.code]
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

    cdef void * _buildPoint(self):
        cdef void *cogr_geometry
        cogr_geometry = ograpi.OGR_G_CreateGeometry(1)
        if self.ndims > 2:
            x, y, z = self.coordinates
            ograpi.OGR_G_AddPoint(cogr_geometry, x, y, z)
        else:
            x, y = self.coordinates
            ograpi.OGR_G_AddPoint_2D(cogr_geometry, x, y)
        return cogr_geometry
    
    cdef void * _buildLineString(self):
        cdef void *cogr_geometry
        cogr_geometry = ograpi.OGR_G_CreateGeometry(2)
        for values in self.coordinates:
            log.debug("Adding point %s", values)
            if len(values) > 2:
                x, y, z = values
                ograpi.OGR_G_AddPoint(cogr_geometry, x, y, z)
            else:
                x, y = values
                ograpi.OGR_G_AddPoint_2D(cogr_geometry, x, y)
        return cogr_geometry
    
    cdef void * _buildLinearRing(self):
        cdef void *cogr_geometry
        cogr_geometry = ograpi.OGR_G_CreateGeometry(101)
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
    
    cdef void * _buildPolygon(self):
        cdef void *cogr_ring
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(3)
        self.ndims = len(self.coordinates[0][0])
        for ring in self.coordinates:
            log.debug("Adding ring %s", ring)
            cogr_ring = OGRGeomBuilder().build(
                {'type': 'LinearRing', 'coordinates': ring} )
            log.debug("Built ring")
            ograpi.OGR_G_AddGeometryDirectly(cogr_geometry, cogr_ring)
            log.debug("Added ring %s", ring)
        return cogr_geometry

    cdef void * _buildMultiPoint(self):
        cdef void *cogr_part
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(4)
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

    cdef void * _buildMultiLineString(self):
        cdef void *cogr_part
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(5)
        for line in self.coordinates:
            log.debug("Adding line %s", line)
            cogr_part = OGRGeomBuilder().build(
                {'type': 'LineString', 'coordinates': line} )
            log.debug("Built line")
            ograpi.OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part)
            log.debug("Added line %s", line)
        return cogr_geometry

    cdef void * _buildMultiPolygon(self):
        cdef void *cogr_part
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(6)
        for part in self.coordinates:
            log.debug("Adding polygon %s", part)
            cogr_part = OGRGeomBuilder().build(
                {'type': 'Polygon', 'coordinates': part} )
            log.debug("Built polygon")
            ograpi.OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part)
            log.debug("Added polygon %s", part)
        return cogr_geometry

    cdef void * _buildGeometryCollection(self):
        cdef void *cogr_part
        cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(7)
        for part in self.coordinates:
            log.debug("Adding part %s", part)
            cogr_part = OGRGeomBuilder().build(part)
            log.debug("Built part")
            ograpi.OGR_G_AddGeometryDirectly(cogr_geometry, cogr_part)
            log.debug("Added part %s", part)
        return cogr_geometry

    cdef void * build(self, object geometry):
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
        cdef void *fdefn
        cdef int i
        
        props = {}
        for i in range(ograpi.OGR_F_GetFieldCount(feature)):
            fdefn = ograpi.OGR_F_GetFieldDefnRef(feature, i)
            key = ograpi.OGR_Fld_GetNameRef(fdefn)
            fieldtypename = FIELD_TYPES[ograpi.OGR_Fld_GetType(fdefn)]
            if not fieldtypename:
                raise ValueError(
                    "Invalid field type %s" % ograpi.OGR_Fld_GetType(fdefn))
            # TODO: other types
            fieldtype = FIELD_TYPES_MAP[fieldtypename]
            if fieldtype is IntType:
                props[key] = ograpi.OGR_F_GetFieldAsInteger(feature, i)
            elif fieldtype is FloatType:
                props[key] = ograpi.OGR_F_GetFieldAsDouble(feature, i)
            elif fieldtype is UnicodeType:
                props[key] = unicode(
                    ograpi.OGR_F_GetFieldAsString(feature, i), 'utf-8' )
            else:
                props[key] = None

        cdef void *cogr_geometry = ograpi.OGR_F_GetGeometryRef(feature)
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

    cdef void * build(self, feature, collection):
        cdef WritingSession session
        session = collection.session
        cdef void *cogr_featuredefn = ograpi.OGR_L_GetLayerDefn(session.cogr_layer)
        cdef void *cogr_geometry = OGRGeomBuilder().build(feature['geometry'])
        cdef void *cogr_feature = ograpi.OGR_F_Create(cogr_featuredefn)
        ograpi.OGR_F_SetGeometryDirectly(cogr_feature, cogr_geometry)
        for key, value in feature['properties'].items():
            i = ograpi.OGR_F_GetFieldIndex(cogr_feature, key)
            ptype = type(value) #FIELD_TYPES_MAP[key]
            if ptype is IntType:
                ograpi.OGR_F_SetFieldInteger(cogr_feature, i, value)
            elif ptype is FloatType:
                ograpi.OGR_F_SetFieldDouble(cogr_feature, i, value)
            elif ptype in (UnicodeType, StringType):
                ograpi.OGR_F_SetFieldString(cogr_feature, i, value)
            else:
                raise ValueError("Invalid field type %s" % ptype)
            log.debug("Set field %s: %s" % (key, value))
        return cogr_feature


cdef _deleteOgrFeature(void *cogr_feature):
    """Delete an OGR feature"""
    if cogr_feature != NULL:
        ograpi.OGR_F_Destroy(cogr_feature)
    cogr_feature = NULL


def featureRT(feature, collection):
    # For testing purposes only, leaks the JSON data
    cdef void *cogr_feature = OGRFeatureBuilder().build(feature, collection)
    cdef void *cogr_geometry = ograpi.OGR_F_GetGeometryRef(cogr_feature)
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
        self.cogr_layer = ograpi.OGR_DS_GetLayerByName(
            self.cogr_ds, collection.name
            )

    def stop(self):
        self.cogr_layer = NULL
        if self.cogr_ds != NULL:
            ograpi.OGR_DS_Destroy(self.cogr_ds)
        self.cogr_ds = NULL

    def get_length(self):
        return ograpi.OGR_L_GetFeatureCount(self.cogr_layer, 0)

    def get_schema(self):
        cdef int i
        cdef int n
        cdef void *cogr_featuredefn
        cdef void *cogr_fielddefn
        props = []
        cogr_featuredefn = ograpi.OGR_L_GetLayerDefn(self.cogr_layer)
        n = ograpi.OGR_FD_GetFieldCount(cogr_featuredefn)
        for i from 0 <= i < n:
            cogr_fielddefn = ograpi.OGR_FD_GetFieldDefn(cogr_featuredefn, i)
            fieldtypename = FIELD_TYPES[ograpi.OGR_Fld_GetType(cogr_fielddefn)]
            if not fieldtypename:
                raise ValueError(
                    "Invalid field type %s" % ograpi.OGR_Fld_GetType(
                                                cogr_fielddefn))
            key = ograpi.OGR_Fld_GetNameRef(cogr_fielddefn)
            props.append((key, fieldtypename))
        geom_type = ograpi.OGR_FD_GetGeomType(cogr_featuredefn)
        return {'properties': dict(props), 'geometry': GEOMETRY_TYPES[geom_type]}

    def isactive(self):
        if self.cogr_layer != NULL and self.cogr_ds != NULL:
            return 1
        else:
            return 0


cdef class WritingSession(Session):
    
    def start(self, collection):
        cdef void *cogr_fielddefn
        cdef void *cogr_driver
        path = collection.path

        if collection.mode == 'a':
            if os.path.exists(path):
                self.cogr_ds = ograpi.OGROpen(path, 1, NULL)
                if self.cogr_ds == NULL:
                    raise RuntimeError("Failed to open %s" % path)
                cogr_driver = ograpi.OGR_DS_GetDriver(self.cogr_ds)
                self.cogr_layer = ograpi.OGR_DS_GetLayerByName(
                                        self.cogr_ds, collection.name)
                if self.cogr_layer == NULL:
                    raise RuntimeError(
                        "Failed to get layer %s" % collection.name)
            else:
                raise OSError("No such file or directory %s" % path)

        elif collection.mode == 'w':
            if os.path.exists(path):
                self.cogr_ds = ograpi.OGROpen(path, 0, NULL)
                if self.cogr_ds != NULL:
                    cogr_driver = ograpi.OGR_DS_GetDriver(self.cogr_ds)
                    ograpi.OGR_DS_Destroy(self.cogr_ds)
                    ograpi.OGR_Dr_DeleteDataSource(cogr_driver, path)
                    log.debug("Deleted pre-existing data at %s", path)
            cogr_driver = ograpi.OGRGetDriverByName(collection.driver)
            self.cogr_ds = ograpi.OGR_Dr_CreateDataSource(
                cogr_driver, path, NULL)
            if self.cogr_ds == NULL:
                raise RuntimeError("Failed to open %s" % path)
            
            self.cogr_layer = ograpi.OGR_DS_CreateLayer(
                self.cogr_ds, 
                collection.name,
                NULL,
                GEOMETRY_TYPES.index(collection.schema['geometry']),
                NULL
                )
            log.debug("Created layer")
            
            for key, value in collection.schema['properties'].items():
                log.debug("Creating field: %s %s", key, value)
                cogr_fielddefn = ograpi.OGR_Fld_Create(
                    key, 
                    FIELD_TYPES.index(value) )
                ograpi.OGR_L_CreateField(self.cogr_layer, cogr_fielddefn, 1)
                ograpi.OGR_Fld_Destroy(cogr_fielddefn)
            log.debug("Created fields")

        log.debug("Writing started")

    def write(self, feature, collection):
        log.debug("Creating feature in layer: %s" % feature)
        try:
            for key in feature['properties']:
                assert key in collection.schema['properties']
            assert feature['geometry']['type'] == collection.schema['geometry']
        except AssertionError:
            raise ValueError("Feature data not match collection schema")
        
        cdef void *cogr_layer = self.cogr_layer
        cdef void *cogr_feature = OGRFeatureBuilder().build(feature, collection)
        result = ograpi.OGR_L_CreateFeature(cogr_layer, cogr_feature)
        if result != OGRERR_NONE:
            raise RuntimeError("Failed to add feature: %s" % result)
        _deleteOgrFeature(cogr_feature)
        return result


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

# Ensure that errors end up in the python session's stdout
cdef void * errorHandler(eErrClass, int err_no, char *msg):
    print msg

