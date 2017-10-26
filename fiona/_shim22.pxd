include "ogrext2.pxd"

cdef bint is_field_null(void *feature, int n)
cdef void gdal_flush_cache(void *cogr_ds)
cdef void* gdal_open_vector(char* path_c, int mode, drivers)
cdef void* gdal_create(void* cogr_driver, const char *path_c) except *
