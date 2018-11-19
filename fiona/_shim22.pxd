include "ogrext2.pxd"

cdef bint is_field_null(void *feature, int n)
cdef void set_field_null(void *feature, int n)
cdef void gdal_flush_cache(void *cogr_ds)
cdef void* gdal_open_vector(const char *path_c, int mode, drivers, options) except NULL
cdef void* gdal_create(void* cogr_driver, const char *path_c, options) except NULL
cdef OGRErr gdal_start_transaction(void *cogr_ds, int force)
cdef OGRErr gdal_commit_transaction(void *cogr_ds)
cdef OGRErr gdal_rollback_transaction(void *cogr_ds)
cdef OGRFieldSubType get_field_subtype(void *fielddefn)
cdef void set_field_subtype(void *fielddefn, OGRFieldSubType subtype)
cdef bint check_capability_create_layer(void *cogr_ds)
cdef void *get_linear_geometry(void *geom)
