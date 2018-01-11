from fiona.ogrext2 cimport *
from fiona._err import cpl_errs

import logging


log = logging.getLogger(__name__)


cdef bint is_field_null(void *feature, int n):
    if not OGR_F_IsFieldSet(feature, n):
        return True
    else:
        return False


cdef void gdal_flush_cache(void *cogr_ds):
    with cpl_errs:
        GDALFlushCache(cogr_ds)


cdef void* gdal_open_vector(char* path_c, int mode, drivers, options):
    cdef void* cogr_ds = NULL
    cdef char **drvs = NULL
    cdef char **open_opts = NULL
    cdef unsigned int flags

    flags = GDAL_OF_VECTOR | GDAL_OF_VERBOSE_ERROR
    if mode == 1:
        flags |= GDAL_OF_UPDATE
    else:
        flags |= GDAL_OF_READONLY

    if drivers:
        for name in drivers:
            name_b = name.encode()
            name_c = name_b
            #log.debug("Trying driver: %s", name)
            drv = GDALGetDriverByName(name_c)
            if drv != NULL:
                drvs = CSLAddString(drvs, name_c)

    for k, v in options.items():
        k = k.upper().encode('utf-8')
        if isinstance(v, bool):
            v = ('ON' if v else 'OFF').encode('utf-8')
        else:
            v = str(v).encode('utf-8')
        log.debug("Set option %r: %r", k, v)
        open_opts = CSLAddNameValue(open_opts, <const char *>k, <const char *>v)

    open_opts = CSLAddNameValue(open_opts, "VALIDATE_OPEN_OPTIONS", "NO")

    try:
        cogr_ds = GDALOpenEx(
            path_c, flags, <const char *const *>drvs, open_opts, NULL)
    except:
        raise
    else:
        return cogr_ds
    finally:
        CSLDestroy(drvs)
        CSLDestroy(open_opts)


cdef void* gdal_create(void* cogr_driver, const char *path_c, options) except *:
    cdef char **creation_opts = NULL

    for k, v in options.items():
        k = k.upper().encode('utf-8')
        if isinstance(v, bool):
            v = ('ON' if v else 'OFF').encode('utf-8')
        else:
            v = str(v).encode('utf-8')
        log.debug("Set option %r: %r", k, v)
        creation_opts = CSLAddNameValue(creation_opts, <const char *>k, <const char *>v)

    try:
        return GDALCreate(cogr_driver, path_c, 0, 0, 0, GDT_Unknown, creation_opts)
    finally:
        CSLDestroy(creation_opts)


cdef OGRErr gdal_start_transaction(void* cogr_ds, int force):
    return GDALDatasetStartTransaction(cogr_ds, force)

cdef OGRErr gdal_commit_transaction(void* cogr_ds):
    return GDALDatasetCommitTransaction(cogr_ds)

cdef OGRErr gdal_rollback_transaction(void* cogr_ds):
    return GDALDatasetRollbackTransaction(cogr_ds)

cdef OGRFieldSubType get_field_subtype(void *fielddefn):
    return OGR_Fld_GetSubType(fielddefn)

cdef void set_field_subtype(void *fielddefn, OGRFieldSubType subtype):
    OGR_Fld_SetSubType(fielddefn, subtype)
