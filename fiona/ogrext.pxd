from libc.stdio cimport FILE


cdef extern from "cpl_vsi.h" nogil:
    ctypedef int vsi_l_offset
    ctypedef FILE VSILFILE


cdef class MemoryFileBase:
    cdef VSILFILE * _vsif
