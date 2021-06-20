# Coordinate system and transform API functions.
include "gdal.pxi"

cdef extern from "ogr_srs_api.h":
    ctypedef enum OSRAxisMappingStrategy:
        OAMS_TRADITIONAL_GIS_ORDER

    void OSRSetAxisMappingStrategy(OGRSpatialReferenceH hSRS, OSRAxisMappingStrategy)
    OGRErr OSRExportToWktEx(OGRSpatialReferenceH, char ** ppszResult,
                            const char* const* papszOptions)

cdef void osr_set_traditional_axis_mapping_strategy(OGRSpatialReferenceH hSrs)
