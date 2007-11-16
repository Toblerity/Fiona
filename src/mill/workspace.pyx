# Copyright (c) 2007, Sean C. Gillies
# All rights reserved.
# See ../LICENSE.txt

cimport ograpi

from mill import ogrinit
from mill.collection import Collection


cdef class Workspace:

    # Path to actual data storage
    cdef public path
    # Feature collections
    cdef _collections

    def __init__(self, path):
        self.path = path
        self._collections = None

    def _read_collections(self):
        cdef void * cogr_ds
        cdef void * cogr_layer
        cdef void * cogr_layerdefn
        collections = {}

        # start session
        cogr_ds = ograpi.OGROpen(self.path, 0, NULL)

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


def workspace(path):
    return Workspace(path)

