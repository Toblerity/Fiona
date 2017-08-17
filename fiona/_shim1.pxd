include "ogrext1.pxd"

cdef bint is_field_null(void *feature, int n)
cdef void gdal_flush_cache(void *cogr_ds)
cdef void* gdal_open_vector(char* path_c, int mode, drivers)
cdef void* gdal_create(void* cogr_driver, const char *path_c) except *

from fiona._shim cimport OGR_F_GetFieldAsInteger as OGR_F_GetFieldAsInteger64
from fiona._shim cimport OGR_F_SetFieldInteger as OGR_F_SetFieldInteger64
from fiona._shim cimport OGR_DS_GetLayerByName as GDALDatasetGetLayerByName
from fiona._shim cimport OGR_DS_GetLayer as GDALDatasetGetLayer
from fiona._shim cimport OGR_DS_Destroy as GDALClose
from fiona._shim cimport OGR_DS_GetDriver as GDALGetDatasetDriver
from fiona._shim cimport OGRGetDriverByName as GDALGetDriverByName
from fiona._shim cimport OGR_DS_GetLayerCount as GDALDatasetGetLayerCount
from fiona._shim cimport OGR_DS_DeleteLayer as GDALDatasetDeleteLayer
from fiona._shim cimport OGR_DS_CreateLayer as GDALDatasetCreateLayer
from fiona._shim cimport OGR_Dr_DeleteDataSource as GDALDeleteDataset
