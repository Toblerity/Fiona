include "ogrext1.pxd"

ctypedef enum OGRFieldSubType:
    OFSTNone = 0
    OFSTBoolean = 1
    OFSTInt16 = 2
    OFSTFloat32 = 3
    OFSTMaxSubType = 3

cdef bint is_field_null(void *feature, int n)
cdef void set_field_null(void *feature, int n)
cdef void gdal_flush_cache(void *cogr_ds)
cdef void* gdal_open_vector(const char* path_c, int mode, drivers, options) except NULL
cdef void* gdal_create(void* cogr_driver, const char *path_c, options) except NULL
cdef bint check_capability_transaction(void *cogr_ds)
cdef OGRErr gdal_start_transaction(void *cogr_ds, int force)
cdef OGRErr gdal_commit_transaction(void *cogr_ds)
cdef OGRErr gdal_rollback_transaction(void *cogr_ds)
cdef OGRFieldSubType get_field_subtype(void *fielddefn)
cdef void set_field_subtype(void *fielddefn, OGRFieldSubType subtype)
cdef bint check_capability_create_layer(void *cogr_ds)
cdef void *get_linear_geometry(void *geom)
cdef const char* osr_get_name(OGRSpatialReferenceH hSrs)
cdef void osr_set_traditional_axis_mapping_strategy(OGRSpatialReferenceH hSrs)
cdef void set_proj_search_path(object path)
cdef void get_proj_version(int *, int *, int *)
cdef void set_field_datetime(void *cogr_feature, int iField, int nYear, int nMonth, int nDay, int nHour, int nMinute, float fSecond, int nTZFlag)
cdef int get_field_as_datetime(void *cogr_feature, int iField, int *, int *, int *, int *, int *, float *, int *)

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
