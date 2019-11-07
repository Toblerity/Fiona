"""Extension module supporting crs.py.

Calls methods from GDAL's OSR module.
"""

from __future__ import absolute_import

import logging

from six import string_types

from fiona cimport _cpl
from fiona._err cimport exc_wrap_pointer
from fiona._err import CPLE_BaseError
from fiona._shim cimport osr_get_name, osr_set_traditional_axis_mapping_strategy
from fiona.compat import DICT_TYPES
from fiona.errors import CRSError


logger = logging.getLogger(__name__)

cdef int OAMS_TRADITIONAL_GIS_ORDER = 0


# Export a WKT string from input crs.
def crs_to_wkt(crs):
    """Convert a Fiona CRS object to WKT format"""
    cdef OGRSpatialReferenceH cogr_srs = NULL
    cdef char *proj_c = NULL

    try:
        cogr_srs = exc_wrap_pointer(OSRNewSpatialReference(NULL))
    except CPLE_BaseError as exc:
        raise CRSError(u"{}".format(exc))

    # First, check for CRS strings like "EPSG:3857".
    if isinstance(crs, string_types):
        proj_b = crs.encode('utf-8')
        proj_c = proj_b
        OSRSetFromUserInput(cogr_srs, proj_c)

    elif isinstance(crs, DICT_TYPES):
        # EPSG is a special case.
        init = crs.get('init')
        if init:
            logger.debug("Init: %s", init)
            auth, val = init.split(':')
            if auth.upper() == 'EPSG':
                logger.debug("Setting EPSG: %s", val)
                OSRImportFromEPSG(cogr_srs, int(val))
        else:
            params = []
            crs['wktext'] = True
            for k, v in crs.items():
                if v is True or (k in ('no_defs', 'wktext') and v):
                    params.append("+%s" % k)
                else:
                    params.append("+%s=%s" % (k, v))
            proj = " ".join(params)
            logger.debug("PROJ.4 to be imported: %r", proj)
            proj_b = proj.encode('utf-8')
            proj_c = proj_b
            OSRImportFromProj4(cogr_srs, proj_c)

    else:
        raise CRSError("Invalid input to create CRS: {}".format(crs))

    osr_set_traditional_axis_mapping_strategy(cogr_srs)
    OSRExportToWkt(cogr_srs, &proj_c)

    if proj_c == NULL:
        raise CRSError("Invalid input to create CRS: {}".format(crs))

    proj_b = proj_c
    _cpl.CPLFree(proj_c)

    if not proj_b:
        raise CRSError("Invalid input to create CRS: {}".format(crs))

    return proj_b.decode('utf-8')
