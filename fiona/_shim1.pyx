"""Shims on top of ogrext for GDAL versions < 2"""

import os

from fiona.ogrext1 cimport *
from fiona._err cimport exc_wrap_pointer
from fiona._err import cpl_errs, CPLE_BaseError, FionaNullPointerError
from fiona.errors import DriverError


cdef int OGRERR_NONE = 0


cdef bint is_field_null(void *feature, int n):
    if not OGR_F_IsFieldSet(feature, n):
        return True
    else:
        return False


cdef void set_field_null(void *feature, int n):
    pass


cdef void gdal_flush_cache(void *cogr_ds):
    retval = OGR_DS_SyncToDisk(cogr_ds)
    if retval != OGRERR_NONE:
        raise RuntimeError("Failed to sync to disk")


cdef void* gdal_open_vector(const char *path_c, int mode, drivers, options) except NULL:
    cdef void* cogr_ds = NULL
    cdef void* drv = NULL
    cdef void* ds = NULL

    encoding = options.get('encoding', None)
    if encoding:
        val = encoding.encode('utf-8')
        CPLSetThreadLocalConfigOption('SHAPE_ENCODING', <const char *>val)
    else:
        CPLSetThreadLocalConfigOption('SHAPE_ENCODING', "")

    if drivers:
        for name in drivers:
            name_b = name.encode()
            name_c = name_b
            drv = OGRGetDriverByName(name_c)
            if drv != NULL:
                ds = OGR_Dr_Open(drv, path_c, mode)
            if ds != NULL:
                cogr_ds = ds
                break
    else:
        cogr_ds = OGROpen(path_c, mode, NULL)

    try:
        return exc_wrap_pointer(cogr_ds)
    except FionaNullPointerError:
        raise DriverError("Failed to open dataset (mode={}): {}".format(mode, path_c.decode("utf-8")))
    except CPLE_BaseError as exc:
        raise DriverError(str(exc))


cdef void* gdal_create(void* cogr_driver, const char *path_c, options) except NULL:
    cdef void* cogr_ds = NULL
    cdef char **opts = NULL

    encoding = options.get('encoding', None)
    if encoding:
        val = encoding.encode('utf-8')
        CPLSetThreadLocalConfigOption('SHAPE_ENCODING', val)
    else:
        CPLSetThreadLocalConfigOption('SHAPE_ENCODING', "")

    for k, v in options.items():
        k = k.upper().encode('utf-8')
        if isinstance(v, bool):
            v = ('ON' if v else 'OFF').encode('utf-8')
        else:
            v = str(v).encode('utf-8')
        opts = CSLAddNameValue(opts, <const char *>k, <const char *>v)

    try:
        return exc_wrap_pointer(
            OGR_Dr_CreateDataSource(cogr_driver, path_c, opts)
        )
    except FionaNullPointerError:
        raise DriverError("Failed to create dataset: {}".format(path_c.decode("utf-8")))
    except CPLE_BaseError as exc:
        raise DriverError(str(exc))
    finally:
        CSLDestroy(opts)


# transactions are not supported in GDAL 1.x
cdef OGRErr gdal_start_transaction(void* cogr_ds, int force):
    return OGRERR_NONE


cdef OGRErr gdal_commit_transaction(void* cogr_ds):
    return OGRERR_NONE


cdef OGRErr gdal_rollback_transaction(void* cogr_ds):
    return OGRERR_NONE


# field subtypes are not supported in GDAL 1.x
cdef OGRFieldSubType get_field_subtype(void *fielddefn):
    return OFSTNone


cdef void set_field_subtype(void *fielddefn, OGRFieldSubType subtype):
    pass


cdef bint check_capability_create_layer(void *cogr_ds):
    return OGR_DS_TestCapability(cogr_ds, ODsCCreateLayer)


cdef void *get_linear_geometry(void *geom):
    return geom


cdef const char* osr_get_name(OGRSpatialReferenceH hSrs):
    return ''


cdef void osr_set_traditional_axis_mapping_strategy(OGRSpatialReferenceH hSrs):
    OSRFixup(hSrs)


cdef void set_proj_search_path(object path):
    os.environ["PROJ_LIB"] = path


cdef (int, int, int) get_proj_version():
    return (-1, -1, -1)
