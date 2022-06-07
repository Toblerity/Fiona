include "gdal.pxi"


cdef extern from "ogr_srs_api.h":
    void OSRSetPROJSearchPaths(const char *const *papszPaths)
    void OSRGetPROJVersion	(int *pnMajor, int *pnMinor, int *pnPatch)


cdef class ConfigEnv(object):
    cdef public object options


cdef class GDALEnv(ConfigEnv):
    cdef public object _have_registered_drivers


cdef _safe_osr_release(OGRSpatialReferenceH srs)
