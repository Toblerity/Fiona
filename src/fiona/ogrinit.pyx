# This module initializes the OGR/CPL environment

import atexit
import logging

cdef extern from "cpl_error.h":
    void    CPLSetErrorHandler (void *handler)
    void *  CPLQuietErrorHandler

cdef extern from "ogr_api.h":
    void OGRRegisterAll()
    void OGRCleanupAll()

code_map = {0: 0, 1: logging.DEBUG, 2: logging.WARNING, 3: logging.ERROR, 4: logging.CRITICAL}
logger = logging.getLogger("Fiona")

cdef void * errorHandler(int eErrClass, int err_no, char *msg):
    logger.log(code_map[eErrClass], "OGR Error %s: %s", err_no, msg)

def setup():
    CPLSetErrorHandler(<void *>errorHandler)
    OGRRegisterAll()

def cleanup():
    OGRCleanupAll()
    CPLSetErrorHandler(NULL)

atexit.register(cleanup)
setup()


