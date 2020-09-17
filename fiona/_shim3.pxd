include "ogrext3.pxd"

cdef bint is_field_null(void *feature, int n)
cdef void set_field_null(void *feature, int n)
cdef void gdal_flush_cache(void *cogr_ds)
cdef void* gdal_open_vector(const char *path_c, int mode, drivers, options) except NULL
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
