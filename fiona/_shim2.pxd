include "ogrext2.pxd"

cdef bint is_field_null(void *feature, int n)
cdef void set_field_null(void *feature, int n)
cdef void gdal_flush_cache(void *cogr_ds)
cdef void* gdal_open_vector(char* path_c, int mode, drivers, options)
cdef void* gdal_create(void* cogr_driver, const char *path_c, options) except *
cdef OGRErr gdal_start_transaction(void *cogr_ds, int force)
cdef OGRErr gdal_commit_transaction(void *cogr_ds)
cdef OGRErr gdal_rollback_transaction(void *cogr_ds)
cdef OGRFieldSubType get_field_subtype(void *fielddefn)
cdef void set_field_subtype(void *fielddefn, OGRFieldSubType subtype)
