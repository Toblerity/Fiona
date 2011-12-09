# Collection extension module

import logging
import os
import sys
from types import IntType, FloatType, StringType, UnicodeType

cdef extern from "Python.h":
    object  PyString_FromString (char *s)
    object  PyString_FromStringAndSize (char *s, Py_ssize_t len)
    char *  PyString_AsString (string)
    object  PyInt_FromString (char *str, char **pend, int base)

cimport ograpi
import ogrinit

log = logging.getLogger("Fiona")

# Geometry extension classes and functions

geometryTypes = [
    'Unknown', 
    'Point', 'LineString', 'Polygon', 'MultiPoint', 
    'MultiLineString', 'MultiPolygon', 'GeometryCollection',
    'None', 'LinearRing', 
    'Point25D', 'LineString25D', 'Polygon25D', 'MultiPoint25D', 
    'MultiLineString25D', 'MultiPolygon25D', 'GeometryCollection25D'
    ]

fieldTypes = [
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

fieldTypesMap = {
    'int':      IntType,
    'float':    FloatType,
    'str':      UnicodeType,
    }

cdef void * _createOgrGeomFromWKB(object wkb):
    """Make an OGR geometry from a WKB string"""
    geom_type = bytearray(wkb)[1]
    cdef unsigned char *buffer = wkb
    cdef void *cogr_geometry = ograpi.OGR_G_CreateGeometry(geom_type)
    ograpi.OGR_G_ImportFromWkb(cogr_geometry, buffer, len(wkb))
    return cogr_geometry

cdef _deleteOgrGeom(void *cogr_geometry):
    """Delete an OGR geometry"""
    ograpi.OGR_G_DestroyGeometry(cogr_geometry)

cdef class GeomBuilder:
    """Builds Fiona (GeoJSON) geometries from an OGR geometry handle."""
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
    cdef build(self, void *geom):
        # The only method anyone needs to call
        self.code = ograpi.OGR_G_GetGeometryType(geom)
        self.typename = geometryTypes[self.code]
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

    cdef object coordinates
    cdef object typename
    cdef object ndims

    cdef void * _buildPoint(self):
        cdef void *cogr_geometry
        self.ndims = len(self.coordinates)
        cogr_geometry = ograpi.OGR_G_CreateGeometry(1)
        if self.ndims > 2:
            x, y, z = self.coordinates
            ograpi.OGR_G_AddPoint(cogr_geometry, x, y, z)
        else:
            x, y = self.coordinates
            ograpi.OGR_G_AddPoint_2D(cogr_geometry, x, y)
        return cogr_geometry
    cdef void * build(self, object geometry):
        self.typename = geometry['type']
        self.coordinates = geometry['coordinates']
        if self.typename == 'Point':
            return self._buildPoint()


cdef geometry(void *geom):
    """Factory for Fiona geometries"""
    return GeomBuilder().build(geom)

# Feature extension classes and functions

cdef class FeatureBuilder:

    cdef build(self, void *feature):
        # The only method anyone ever needs to call
        cdef void *fdefn
        cdef int i
        
        props = {}
        for i in range(ograpi.OGR_F_GetFieldCount(feature)):
            fdefn = ograpi.OGR_F_GetFieldDefnRef(feature, i)
            key = ograpi.OGR_Fld_GetNameRef(fdefn)
            fieldtypename = fieldTypes[ograpi.OGR_Fld_GetType(fdefn)]
            if not fieldtypename:
                raise ValueError(
                    "Invalid field type %s" % ograpi.OGR_Fld_GetType(fdefn))
            # TODO: other types
            fieldtype = fieldTypesMap[fieldtypename]
            if fieldtype is IntType:
                props[key] = ograpi.OGR_F_GetFieldAsInteger(feature, i)
            elif fieldtype is FloatType:
                props[key] = ograpi.OGR_F_GetFieldAsDouble(feature, i)
            elif fieldtype is UnicodeType:
                props[key] = unicode(ograpi.OGR_F_GetFieldAsString(feature, i))
            else:
                props[key] = None

        cdef void *cogr_geometry = ograpi.OGR_F_GetGeometryRef(feature)
        geom = GeomBuilder().build(cogr_geometry)
        
        return {
            'id': str(ograpi.OGR_F_GetFID(feature)),
            'geometry': geom,
            'properties': props }


cdef class OGRFeatureBuilder:
    
    #cdef void *cogr_featuredefn

    cdef void * build(self, feature, collection):
        cdef WriteSession session
        session = collection.session
        cdef void *cogr_featuredefn = ograpi.OGR_L_GetLayerDefn(session.cogr_layer)
        cdef void *cogr_geometry = OGRGeomBuilder().build(feature['geometry'])
        cdef void *cogr_feature = ograpi.OGR_F_Create(cogr_featuredefn)
        ograpi.OGR_F_SetGeometryDirectly(cogr_feature, cogr_geometry)
        for key, value in feature['properties'].items():
            i = ograpi.OGR_F_GetFieldIndex(cogr_feature, key)
            ptype = type(value)
            if ptype is IntType:
                ograpi.OGR_F_SetFieldInteger(cogr_feature, i, value)
            elif ptype is FloatType:
                ograpi.OGR_F_SetFieldDouble(cogr_feature, i, value)
            if ptype in (UnicodeType, StringType):
                ograpi.OGR_F_SetFieldString(cogr_feature, i, value)
            else:
                raise ValueError("Invalid field type %s" % ptype)

            log.debug("Set field %s: %s" % (key, value))

        return cogr_feature

def featureRT(feature, collection):
    # For testing purposes
    cdef void *cogr_feature = OGRFeatureBuilder().build(feature, collection)
    cdef void *cogr_geometry = ograpi.OGR_F_GetGeometryRef(cogr_feature)
    log.debug("Geometry: %s" % ograpi.OGR_G_ExportToJson(cogr_geometry))
    return FeatureBuilder().build(cogr_feature)


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
        self.cogr_ds = ograpi.OGROpen(collection.workspace.path, 0, NULL)
        self.cogr_layer = ograpi.OGR_DS_GetLayerByName(
            self.cogr_ds, collection.name
            )

    def stop(self):
        self.cogr_layer = NULL
        if self.cogr_ds != NULL:
            ograpi.OGR_DS_Destroy(self.cogr_ds)
        self.cogr_ds = NULL

    cdef isactive(self):
        if self.cogr_layer != NULL and self.cogr_ds != NULL:
            return 1
        else:
            return 0


cdef class WriteSession:
    
    cdef void *cogr_ds
    cdef void *cogr_layer

    def __cinit__(self):
        self.cogr_ds = NULL
        self.cogr_layer = NULL

    def __dealloc__(self):
        self.stop()

    def start(self, collection):
        cdef void *cogr_fielddefn
        cdef void *cogr_driver
        path = collection.workspace.path
        
        # Presume we have a collection schema already (evaluate this)
        if not collection.schema:
            raise ValueError("A collection schema has not been defined")
        
        if collection.mode == 'a':
            if not os.path.exists(path):
                cogr_driver = ograpi.OGRGetDriverByName(collection.driver)
                self.cogr_ds = ograpi.OGR_Dr_CreateDataSource(
                    cogr_driver, path, NULL)
            else:
                self.cogr_ds = ograpi.OGROpen(path, 1, NULL)
                cogr_driver = ograpi.OGR_DS_GetDriver(self.cogr_ds)
        elif collection.mode == 'w':
            cogr_driver = ograpi.OGRGetDriverByName(collection.driver)
            if os.path.exists(path):
                ograpi.OGR_Dr_DeleteDataSource(cogr_driver, path)
            self.cogr_ds = ograpi.OGR_Dr_CreateDataSource(
                cogr_driver, collection.workspace.path, NULL)
        if not self.cogr_ds:
            raise RuntimeError("Failed to open %s" % collection.workspace.path)
        log.debug("Created datasource")
        
        self.cogr_layer = ograpi.OGR_DS_CreateLayer(
            self.cogr_ds, 
            collection.name,
            NULL,
            geometryTypes.index(collection.schema['geometry']),
            NULL
            )
        log.debug("Created layer")

        for key, value in collection.schema['properties'].items():
            log.debug("Creating field: %s %s", key, value)
            cogr_fielddefn = ograpi.OGR_Fld_Create(
                key, 
                fieldTypes.index(value) )
            ograpi.OGR_L_CreateField(self.cogr_layer, cogr_fielddefn, 1)
        log.debug("Created fields")

    def stop(self):
        self.cogr_layer = NULL
        if self.cogr_ds != NULL:
            ograpi.OGR_DS_Destroy(self.cogr_ds)
        self.cogr_ds = NULL

    cdef isactive(self):
        if self.cogr_layer != NULL and self.cogr_ds != NULL:
            return 1
        else:
            return 0


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

    def __del__(self):
        pass #self._session.stop()
        
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
        ograpi.OGR_F_Destroy(cogr_feature)
        return feature


cdef class Writer:

    # Reference to its Collection
    cdef collection

    def __init__(self, collection):
        if collection.session is None:
            raise ValueError("I/O operation on closed collection")
        self.collection = collection

    def write(self, feature):
        cdef long fid
        cdef void * cogr_feature
        cdef WriteSession session

        # Make sure feature matches schema
        try:
            for key in feature['properties']:
                assert key in self.collection.schema['properties']
        except AssertionError:
            raise ValueError("Feature's properties do not match collection schema")

        # feature -> JSON -> OGR feature
        
        # write OGR feature
        pass


cdef class Collection:

    """A collection of the data records that GIS terms 'features' with
    hybrid list/iterator behavior.
    """

    # Cached length or count of features
    cdef int _len
    # Feature schema, a list of (name, type) tuples
    cdef _schema

    cdef public name
    cdef public workspace
    cdef public mode
    cdef public Session session

    def __init__(self, name, mode='r', workspace=None):
        self.name = name
        self.workspace = workspace
        self.mode = mode
        self.session = None
        self._len = -1
        self._schema = None

    # Context management
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.session:
            self.close()
        self.workspace = None

    def _read_length(self):
        len = ograpi.OGR_L_GetFeatureCount(self.session.cogr_layer, 0)
        return len

    def __len__(self):
        if self._len < 0:
            self._len = self._read_length()
        return self._len

    def _read_schema(self):
        cdef int i
        cdef int n
        cdef void * cogr_featuredefn
        cdef void * cogr_fielddefn
        props = []
        cogr_featuredefn = ograpi.OGR_L_GetLayerDefn(self.session.cogr_layer)
        n = ograpi.OGR_FD_GetFieldCount(cogr_featuredefn)
        for i from 0 <= i < n:
            cogr_fielddefn = ograpi.OGR_FD_GetFieldDefn(cogr_featuredefn, i)
            fieldtypename = fieldTypes[ograpi.OGR_Fld_GetType(cogr_fielddefn)]
            if not fieldtypename:
                raise ValueError(
                    "Invalid field type %s" % ograpi.OGR_Fld_GetType(
                                                cogr_fielddefn))
            key = ograpi.OGR_Fld_GetNameRef(cogr_fielddefn)
            props.append((key, fieldtypename))
        geom_type = ograpi.OGR_FD_GetGeomType(cogr_featuredefn)
        return {'properties': dict(props), 'geometry': geometryTypes[geom_type]}

    def set_schema(self, schema):
        self._schema = schema

    property schema:
        # A lazy property
        def __get__(self):
            if not self._schema:
                self._schema = self._read_schema()
            return self._schema

    def open(self):
        if self.session is not None:
            raise IOError("Collection is already open")
        if self.mode == "r":
            self.session = Session()
            self.session.start(self)
        elif self.mode == "w":
            self.session = WriteSession()
            self.session.start(self)

    def close(self):
        if self.session is None:
            raise IOError("Collection is not open")
        self.session.stop()
        self.session = None

    property opened:
        def __get__(self):
            return self.session is not None

    # Feature reading

    def filter(self, bbox=None):
        return Iterator(self, bbox)

    property all:
        def __get__(self):
            return Iterator(self)

    def __iter__(self):
        return Iterator(self)

    # Feature writing

    def write(self, feature):
        if self.mode != "w" or not self.opened:
            raise IOError("Collection not open for writing")
        

cdef class WriteCollection:

    """A collection of the data records that GIS terms 'features' with
    hybrid list/iterator behavior.
    """

    # Cached length or count of features
    cdef int _len
    # Feature schema, a list of (name, type) tuples
    cdef _schema

    cdef public name
    cdef public workspace
    cdef public mode
    cdef public WriteSession session
    cdef public driver

    def __init__(self, name, mode='a', driver=None, workspace=None):
        self.name = name
        self.workspace = workspace
        self.mode = mode
        self.session = None
        self._len = -1
        self._schema = None
        self.driver = driver

    # Context management
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.session:
            self.close()
        self.workspace = None

    def _read_length(self):
        len = ograpi.OGR_L_GetFeatureCount(self.session.cogr_layer, 0)
        return len

    def __len__(self):
        if self._len < 0:
            self._len = self._read_length()
        return self._len

    def _read_schema(self):
        cdef int i
        cdef int n
        cdef void * cogr_featuredefn
        cdef void * cogr_fielddefn
        props = []
        cogr_featuredefn = ograpi.OGR_L_GetLayerDefn(self.session.cogr_layer)
        n = ograpi.OGR_FD_GetFieldCount(cogr_featuredefn)
        for i from 0 <= i < n:
            cogr_fielddefn = ograpi.OGR_FD_GetFieldDefn(cogr_featuredefn, i)
            fieldtypename = fieldTypes[ograpi.OGR_Fld_GetType(cogr_fielddefn)]
            if not fieldtypename:
                raise ValueError(
                    "Invalid field type %s" % ograpi.OGR_Fld_GetType(
                                                cogr_fielddefn))
            key = ograpi.OGR_Fld_GetNameRef(cogr_fielddefn)
            props.append((key, fieldtypename))
        geom_type = ograpi.OGR_FD_GetGeomType(cogr_featuredefn)
        return {'properties': dict(props), 'geometry': geometryTypes[geom_type]}

    def set_schema(self, schema):
        self._schema = schema

    property schema:
        # A lazy property
        def __get__(self):
            if not self._schema:
                self._schema = self._read_schema()
            return self._schema

    def open(self):
        if self.session is not None:
            raise IOError("Collection is already open")
        self.session = WriteSession(self)
        self.session.start(self)

    def close(self):
        if self.session is None:
            raise IOError("Collection is not open")
        self.session.stop()
        self.session = None

    property opened:
        def __get__(self):
            return self.session is not None

    # Feature reading

    def filter(self, bbox=None):
        return Iterator(self, bbox)

    property all:
        def __get__(self):
            return Iterator(self)

    def __iter__(self):
        return Iterator(self)

    # Feature writing

    def write(self, feature):
        if self.mode != "w" or not self.opened:
            raise IOError("Collection not open for writing")


# Workspace

# Ensure that errors end up in the python session's stdout
cdef void * errorHandler(eErrClass, int err_no, char *msg):
    print msg

cdef class Workspace:

    # Path to actual data storage
    cdef public path
    cdef public mode
    # Feature collections
    cdef _collections

    def __init__(self, path, mode="r"):
        self.path = path
        self.mode = mode
        self._collections = None

    def _read_collections(self):
        cdef void * cogr_ds
        cdef void * cogr_layer
        cdef void * cogr_layerdefn
        collections = {}

        # start session
        cogr_ds = ograpi.OGROpen(self.path, int(self.mode=="r+"), NULL)
        ograpi.CPLSetErrorHandler(<void *>errorHandler)

        n = ograpi.OGR_DS_GetLayerCount(cogr_ds)
        for i in range(n):
            cogr_layer = ograpi.OGR_DS_GetLayer(cogr_ds, i)
            cogr_layerdefn = ograpi.OGR_L_GetLayerDefn(cogr_layer)
            layer_name = ograpi.OGR_FD_GetName(cogr_layerdefn)
            collection = Collection(layer_name, self)
            collections[layer_name] = collection
        
        # end session
        ograpi.OGR_DS_Destroy(cogr_ds)
        
        return collections

    property collections:
        # A lazy property
        def __get__(self):
            if not self._collections:
                self._collections = self._read_collections()
            return self._collections

    def __getitem__(self, name):
        return self.collections.__getitem__(name)

    def keys(self):
        return self.collections.keys()
   
    def values(self):
        return self.collections.values()

    def items(self):
        return self.collections.items()


# Factories

def workspace(path):
    return Workspace(path)

def collection(path, mode='r', driver=None, schema=None, crs=None):
    """Open file at ``path`` in ``mode`` "r" (read) or "a" (append) and
    return a ``Collection`` object."""
    if mode == 'r':
        c = Collection(None, mode)
        c.workspace = Workspace(path, mode)
        c.name = c.workspace.keys()[0]
    elif mode in ('a', 'w'):
        c = WriteCollection(None, mode, driver)
        c.name = os.path.basename(os.path.splitext(path)[0])
        c.workspace = Workspace(path, mode)
    else:
        raise ValueError("Invalid mode: %s" % mode)
    if schema:
        c.set_schema(schema)
    c.open()
    return c

