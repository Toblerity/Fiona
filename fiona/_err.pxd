from libc.stdio cimport *

cdef extern from "cpl_vsi.h":

    ctypedef FILE VSILFILE


cdef void *exc_wrap_pointer(void *ptr) except NULL
cdef VSILFILE *exc_wrap_vsilfile(VSILFILE *f) except NULL
