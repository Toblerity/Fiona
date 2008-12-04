# Copyright (c) 2007, Sean C. Gillies
# All rights reserved.
# See ../LICENSE.txt

cdef extern from "Python.h":
    object  PyString_FromStringAndSize (char *s, Py_ssize_t len)
    char *  PyString_AsString (string)
    object  PyInt_FromString (char *str, char **pend, int base)

cimport ograpi

from mill import ogrinit
from mill.feature import feature


cdef class Session:
    
    cdef void *cogr_ds
    cdef void *cogr_layer

    def __new__(self):
        self.cogr_ds = NULL
        self.cogr_layer = NULL

    def __dealloc__(self):
        self.cogr_layer = NULL
        if self.cogr_ds != NULL:
            ograpi.OGR_DS_Destroy(self.cogr_ds)
        self.cogr_ds = NULL

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


cdef class Iterator:

    """Provides iterated or single item access to feature data within a 
    session.
    """

    # Reference to a Collection
    cdef collection
    # Cached session
    cdef _session
    # Factory for feature instances
    cdef object_hook

    def __init__(self, collection, bbox=None, object_hook=None):
        cdef Session session
        
        self.collection = collection
        session = Session()
        session.start(collection)
        if bbox:
            ograpi.OGR_L_SetSpatialFilterRect(
                session.cogr_layer, bbox[0], bbox[1], bbox[2], bbox[3]
                )
        self.object_hook = object_hook or collection.object_hook
        self._session = session

    def __del__(self):
        self._session.stop()
        
    def __getitem__(self, key):
        # Get feature by id
        cdef void * cogr_feature
        cdef Session session

        session = self._session
        i = PyInt_FromString(key, NULL, 0)
        cogr_feature = ograpi.OGR_L_GetFeature(session.cogr_layer, i)
        f = self._marshal_feature(cogr_feature, i)
        ograpi.OGR_F_Destroy(cogr_feature)
        return f

    def __iter__(self):
        return self

    def __next__(self):
        cdef long fid
        cdef void * cogr_feature
        cdef Session session
        
        session = self._session
        cogr_feature = ograpi.OGR_L_GetNextFeature(session.cogr_layer)
        if cogr_feature == NULL:
            raise StopIteration

        fid = ograpi.OGR_F_GetFID(cogr_feature)
        f = self._marshal_feature(cogr_feature, fid)
        ograpi.OGR_F_Destroy(cogr_feature)
        return f

    cdef _marshal_feature(self, void *cogr_feature, long fid):
        # Marshal the OGR feature via the collection's object hook
        cdef int i
        cdef int n
        cdef void * cogr_geometry
        cdef int wkbsize
        cdef char * buffer
        
        if cogr_feature == NULL:
            return None

        # Produce a properties dict from feature field values
        props = {}
        schema = self.collection.schema
        n = len(schema)
        for i from 0 <= i < n:
            name, fieldtype = schema[i]
            # TODO: other types
            if fieldtype == 0:
                props[name] = ograpi.OGR_F_GetFieldAsInteger(cogr_feature, i)
            elif fieldtype == 2:
                props[name] = ograpi.OGR_F_GetFieldAsDouble(cogr_feature, i)
            elif fieldtype == 4:
                props[name] = ograpi.OGR_F_GetFieldAsString(cogr_feature, i)
            else:
                props[name] = None

        # Marshal the OGR geometry if present
        cogr_geometry = ograpi.OGR_F_GetGeometryRef(cogr_feature)
        if cogr_geometry != NULL:
            wkbsize = ograpi.OGR_G_WkbSize(cogr_geometry)
            string = PyString_FromStringAndSize(NULL, wkbsize)
            buffer = PyString_AsString(string)
            ograpi.OGR_G_ExportToWkb(cogr_geometry, 1, buffer)
        else:
            string = None

        # The object hook protocol calls object_hook with three arguments
        # 
        # 1) string id
        # 2) property dictionary
        # 3) WKB binary string

        f = self.object_hook(
            str(fid),
            props,
            string
            )
        return f


cdef class Collection:

    """A collection of the data records that GIS terms 'features' with
    hybrid list/iterator behavior.
    """

    # Cached length or count of features
    cdef _len
    # Feature schema, a list of (name, type) tuples
    cdef _schema
    # factory for feature instances
    cdef public object_hook

    cdef public name
    cdef public workspace

    def __init__(self, name, workspace=None):
        self.name = name
        self.workspace = workspace
        self.object_hook = feature
        self._len = -1

    def __len__(self):
        if self._len < 0:
            self._len = self._read_length()
        return self._len

    def _read_length(self):
        cdef Session session

        session = Session()
        session.start(self)
        len = ograpi.OGR_L_GetFeatureCount(session.cogr_layer, 0)
        session.stop()
        return len

    def _read_schema(self):
        cdef int i
        cdef int n
        cdef void * cogr_featuredefn
        cdef void * cogr_fielddefn
        cdef Session session

        schema = []
        session = Session()
        session.start(self)
        cogr_featuredefn = ograpi.OGR_L_GetLayerDefn(session.cogr_layer)
        n = ograpi.OGR_FD_GetFieldCount(cogr_featuredefn)
        for i from 0 <= i < n:
            cogr_fielddefn = ograpi.OGR_FD_GetFieldDefn(cogr_featuredefn, i)
            name = ograpi.OGR_Fld_GetNameRef(cogr_fielddefn)
            fieldtype = ograpi.OGR_Fld_GetType(cogr_fielddefn)
            schema.append((name, fieldtype))
        session.stop()
        return schema

    property schema:
        # A lazy property
        def __get__(self):
            if not self._schema:
                self._schema = self._read_schema()
            return self._schema

    def filter(self, bbox=None, object_hook=None):
        return Iterator(self, bbox, object_hook)

    property all:
        def __get__(self):
            return Iterator(self)

    def __iter__(self):
        return Iterator(self)

    def __getitem__(self, key):
        iterator = Iterator(self)
        return iterator[key]

    # TODO: setting items, slicing?
    # A mechanism for sessions, holding the OGR datasource open would reduce
    # the cost of accessing multiple items by index.


def collection(name, workspace=None):
    """Create a new collection."""
    return Collection(name, workspace)

