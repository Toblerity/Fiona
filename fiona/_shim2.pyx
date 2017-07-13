from fiona.ogrext2 cimport *
from fiona._err import cpl_errs

cdef bint is_field_null(void *feature, int n):
    if not OGR_F_IsFieldSet(feature, n):
        return True
    else:
        return False

cdef void gdal_flush_cache(void *cogr_ds):
    with cpl_errs:
        GDALFlushCache(cogr_ds)

cdef void* gdal_open_vector(char* path_c, int mode, drivers):
    if mode == 1:
        mode = GDAL_OF_UPDATE
    else:
        mode = GDAL_OF_READONLY
    cdef void* cogr_ds
    cdef char **drvs = NULL
    if drivers:
        for name in drivers:
            name_b = name.encode()
            name_c = name_b
            #log.debug("Trying driver: %s", name)
            drv = GDALGetDriverByName(name_c)
            if drv != NULL:
                drvs = CSLAddString(drvs, name_c)
    
    flags = GDAL_OF_VECTOR | mode
    try:
        cogr_ds = GDALOpenEx(
            path_c, flags, <const char *const *>drvs, NULL, NULL)
    finally:
        CSLDestroy(drvs)
    return cogr_ds

cdef void* gdal_create(void* cogr_driver, const char *path_c) except *:
    return GDALCreate(
        cogr_driver,
        path_c,
        0,
        0,
        0,
        GDT_Unknown,
        NULL)
