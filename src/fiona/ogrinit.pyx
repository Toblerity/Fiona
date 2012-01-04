# This module initializes the OGR/CPL environment

import atexit
import logging

cdef extern from "cpl_error.h":
    void    CPLSetErrorHandler (void *handler)
    void *  CPLQuietErrorHandler

cdef extern from "ogr_api.h":
    void OGRRegisterAll()
    void OGRCleanupAll()

log = logging.getLogger("Fiona")


# Write OGR errors to the Fiona log
cdef void * errorHandler(eErrClass, int err_no, char *msg):
    log.error("OGR Error %s: %s", err_no, msg)

def setup():
    CPLSetErrorHandler(<void *>errorHandler)
    OGRRegisterAll()

def cleanup():
    OGRCleanupAll()
    CPLSetErrorHandler(NULL)

atexit.register(cleanup)
setup()


