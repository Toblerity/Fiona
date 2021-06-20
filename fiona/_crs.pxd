# Coordinate system and transform API functions.
include "gdal.pxi"


IF CTE_GDAL_MAJOR_VERSION >= 3:

    cdef extern from "ogr_srs_api.h":
        ctypedef enum OSRAxisMappingStrategy:
            OAMS_TRADITIONAL_GIS_ORDER

        void OSRSetAxisMappingStrategy(OGRSpatialReferenceH hSRS, OSRAxisMappingStrategy)

ELSE:

    cdef extern from "ogr_srs_api.h":
        int     OSRFixup (OGRSpatialReferenceH srs)

cdef void osr_set_traditional_axis_mapping_strategy(OGRSpatialReferenceH hSrs)
