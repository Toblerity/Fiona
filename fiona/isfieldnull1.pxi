
cdef extern from "ogr_api.h":

    int OGR_F_IsFieldSet (void *feature, int n)


cdef bint is_field_null(void *feature, int n):
    if not OGR_F_IsFieldSet(feature, n):
        return True
    else:
        return False

