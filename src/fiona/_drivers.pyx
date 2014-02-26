# The GDAL and OGR driver registry.
# GDAL driver management.

cdef extern from "cpl_error.h":
    void    CPLSetErrorHandler (void *handler)

cdef extern from "gdal.h":
    void GDALAllRegister()
    void GDALDestroyDriverManager()
    int GDALGetDriverCount()

cdef extern from "ogr_api.h":
    void OGRRegisterAll()
    void OGRCleanupAll()
    int OGRGetDriverCount()

import logging


log = logging.getLogger('Fiona')
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
log.addHandler(NullHandler())

code_map = {
    0: 0, 
    1: logging.DEBUG, 
    2: logging.WARNING, 
    3: logging.ERROR, 
    4: logging.CRITICAL }

cdef void * errorHandler(int eErrClass, int err_no, char *msg):
    log.log(code_map[eErrClass], "OGR Error %s: %s", err_no, msg)


def driver_count():
    return GDALGetDriverCount() + OGRGetDriverCount()


cdef class DriverManager(object):
    
    def __enter__(self):
        CPLSetErrorHandler(<void *>errorHandler)
        GDALAllRegister()
        OGRRegisterAll()
        if driver_count() == 0:
            raise ValueError("Drivers not registered")
        return self

    def __exit__(self, exc_type=None, exc_val=None, exc_tb=None):
        GDALDestroyDriverManager()
        OGRCleanupAll()
        CPLSetErrorHandler(NULL)
        if driver_count() != 0:
            raise ValueError("Drivers not de-registered")


