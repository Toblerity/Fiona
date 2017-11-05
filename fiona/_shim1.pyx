from fiona.ogrext1 cimport *

from fiona.errors import DriverIOError
from fiona._err cimport exc_wrap_pointer

cdef int OGRERR_NONE = 0

cdef bint is_field_null(void *feature, int n):
    if not OGR_F_IsFieldSet(feature, n):
        return True
    else:
        return False

cdef void gdal_flush_cache(void *cogr_ds):
    retval = OGR_DS_SyncToDisk(cogr_ds)
    if retval != OGRERR_NONE:
        raise RuntimeError("Failed to sync to disk")

cdef void* gdal_open_vector(const char *path_c, int mode, drivers):
    cdef void* cogr_ds = NULL
    cdef void* drv = NULL
    cdef void* ds = NULL
    if drivers:
        for name in drivers:
            name_b = name.encode()
            name_c = name_b
            #log.debug("Trying driver: %s", name)
            drv = OGRGetDriverByName(name_c)
            if drv != NULL:
                ds = OGR_Dr_Open(drv, path_c, mode)
            if ds != NULL:
                cogr_ds = ds
                # TODO
                #collection._driver = name
                break
    else:
        cogr_ds = OGROpen(path_c, mode, NULL)
    return cogr_ds

cdef void* gdal_create(void* cogr_driver, const char *path_c) except *:
    cdef void* cogr_ds
    try:
        cogr_ds = exc_wrap_pointer(
            OGR_Dr_CreateDataSource(
                cogr_driver, path_c, NULL))
    except Exception as exc:
        raise DriverIOError(str(exc))
    return cogr_ds
