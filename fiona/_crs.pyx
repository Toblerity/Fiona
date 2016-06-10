"""Extension module supporting crs.py.

Calls methods from GDAL's OSR module.
"""

import logging

from six import string_types

from fiona cimport _cpl, _crs
from fiona.errors import CRSError


logger = logging.getLogger(__name__)


# Export a WKT string from input crs.
def crs_to_wkt(crs):
    """Convert a Fiona CRS object to WKT format"""
    cdef void *cogr_srs = NULL
    cdef char *proj_c = NULL

    cogr_srs = _crs.OSRNewSpatialReference(NULL)
    if cogr_srs == NULL:
        raise CRSError("NULL spatial reference")

    # First, check for CRS strings like "EPSG:3857".
    if isinstance(crs, string_types):
        proj_b = crs.encode('utf-8')
        proj_c = proj_b
        _crs.OSRSetFromUserInput(cogr_srs, proj_c)
    elif isinstance(crs, dict):
        # EPSG is a special case.
        init = crs.get('init')
        if init:
            logger.debug("Init: %s", init)
            auth, val = init.split(':')
            if auth.upper() == 'EPSG':
                logger.debug("Setting EPSG: %s", val)
                _crs.OSRImportFromEPSG(cogr_srs, int(val))
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
            _crs.OSRImportFromProj4(cogr_srs, proj_c)
    else:
        raise ValueError("Invalid CRS")

    # Fixup, export to WKT, and set the GDAL dataset's projection.
    _crs.OSRFixup(cogr_srs)

    _crs.OSRExportToWkt(cogr_srs, &proj_c)

    if proj_c == NULL:
        raise CRSError("Null projection")

    proj_b = proj_c
    _cpl.CPLFree(proj_c)

    return proj_b.decode('utf-8')
