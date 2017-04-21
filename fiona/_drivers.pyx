# The GDAL and OGR driver registry.
# GDAL driver management.

import os
import os.path
import logging
import sys

from six import string_types


cdef extern from "cpl_conv.h":
    void    CPLFree (void *ptr)
    void    CPLSetThreadLocalConfigOption (char *key, char *val)
    const char * CPLGetConfigOption ( const char *key, const char *default)


cdef extern from "cpl_error.h":
    void CPLSetErrorHandler (void *handler)


cdef extern from "gdal.h":
    void GDALAllRegister()
    void GDALDestroyDriverManager()
    int GDALGetDriverCount()
    void * GDALGetDriver(int i)
    const char * GDALGetDriverShortName(void *driver)
    const char * GDALGetDriverLongName(void *driver)


cdef extern from "ogr_api.h":
    void OGRRegisterDriver(void *driver)
    void OGRDeregisterDriver(void *driver)
    void OGRRegisterAll()
    void OGRCleanupAll()
    int OGRGetDriverCount()
    void * OGRGetDriver(int i)
    void * OGRGetDriverByName(const char *name)
    const char * OGR_Dr_GetName(void *driver)


log = logging.getLogger('Fiona')
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
log.addHandler(NullHandler())


level_map = {
    0: 0,
    1: logging.DEBUG,
    2: logging.WARNING,
    3: logging.ERROR,
    4: logging.CRITICAL }

code_map = {
    0: 'CPLE_None',
    1: 'CPLE_AppDefined',
    2: 'CPLE_OutOfMemory',
    3: 'CPLE_FileIO',
    4: 'CPLE_OpenFailed',
    5: 'CPLE_IllegalArg',
    6: 'CPLE_NotSupported',
    7: 'CPLE_AssertionFailed',
    8: 'CPLE_NoWriteAccess',
    9: 'CPLE_UserInterrupt',
    10: 'CPLE_ObjectNull'
}


IF UNAME_SYSNAME == "Windows":
    cdef void * __stdcall errorHandler(int eErrClass, int err_no, char *msg):
        log.log(level_map[eErrClass], "%s in %s", code_map[err_no], msg)
ELSE:
    cdef void * errorHandler(int eErrClass, int err_no, char *msg):
        log.log(level_map[eErrClass], "%s in %s", code_map[err_no], msg)


def driver_count():
    return OGRGetDriverCount()


cdef class GDALEnv(object):

    cdef public object options

    def __init__(self, **options):
        self.options = options.copy()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        self.stop()

    def start(self):
        cdef const char *key_c = NULL
        cdef const char *val_c = NULL

        if GDALGetDriverCount() == 0:
            GDALAllRegister()
        if OGRGetDriverCount() == 0:
            OGRRegisterAll()
        CPLSetErrorHandler(<void *>errorHandler)
        if OGRGetDriverCount() == 0:
            raise ValueError("Drivers not registered")

        if 'GDAL_DATA' not in os.environ:
            whl_datadir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "gdal_data"))
            share_datadir = os.path.join(sys.prefix, 'share/gdal')
            if os.path.exists(os.path.join(whl_datadir, 'pcs.csv')):
                os.environ['GDAL_DATA'] = whl_datadir
            elif os.path.exists(os.path.join(share_datadir, 'pcs.csv')):
                os.environ['GDAL_DATA'] = share_datadir
        if 'PROJ_LIB' not in os.environ:
            whl_datadir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "proj_data"))
            share_datadir = os.path.join(sys.prefix, 'share/proj')
            if os.path.exists(whl_datadir):
                os.environ['PROJ_LIB'] = whl_datadir
            elif os.path.exists(share_datadir):
                os.environ['PROJ_LIB'] = share_datadir

        for key, val in self.options.items():
            key_b = key.upper().encode('utf-8')
            key_c = key_b
            if isinstance(val, string_types):
                val_b = val.encode('utf-8')
            else:
                val_b = ('ON' if val else 'OFF').encode('utf-8')
            val_c = val_b
            CPLSetThreadLocalConfigOption(key_c, val_c)
            log.debug("Option %s=%s", key, CPLGetConfigOption(key_c, NULL))
        return self

    def stop(self):
        cdef const char *key_c = NULL
        for key in self.options:
            key_b = key.upper().encode('utf-8')
            key_c = key_b
            CPLSetThreadLocalConfigOption(key_c, NULL)
        CPLSetErrorHandler(NULL)

    def drivers(self):
        cdef void *drv = NULL
        cdef char *key = NULL
        cdef char *val = NULL
        cdef int i
        result = {}
        for i in range(OGRGetDriverCount()):
            drv = OGRGetDriver(i)
            key = OGR_Dr_GetName(drv)
            key_b = key
            val = OGR_Dr_GetName(drv)
            val_b = val
            result[key_b.decode('utf-8')] = val_b.decode('utf-8')
        return result
