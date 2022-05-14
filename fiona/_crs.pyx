"""Extension module supporting crs.py.

Calls methods from GDAL's OSR module.
"""

from __future__ import absolute_import

import logging
import os

from fiona cimport _cpl
from fiona._err cimport exc_wrap_pointer, exc_wrap_ogrerr
from fiona._err import CPLE_BaseError
from fiona.compat import DICT_TYPES
from fiona.errors import CRSError


logger = logging.getLogger(__name__)


cdef void osr_set_traditional_axis_mapping_strategy(OGRSpatialReferenceH hSrs):
    OSRSetAxisMappingStrategy(hSrs, OAMS_TRADITIONAL_GIS_ORDER)


cdef _osr_to_wkt(OGRSpatialReferenceH cogr_srs, crs, wkt_version):
    cdef char *wkt_c = NULL
    wkt = None
    cdef const char* options_wkt[2]
    options_wkt[0] = NULL
    options_wkt[1] = NULL

    if wkt_version:
        wkt_format = f"FORMAT={wkt_version}".encode("utf-8")
        options_wkt[0] = wkt_format

    gdal_error = None
    try:
        exc_wrap_ogrerr(
            OSRExportToWktEx(cogr_srs, &wkt_c, options_wkt)
        )
    except CPLE_BaseError as error:
        gdal_error = error

    if wkt_c != NULL:
        wkt_b = wkt_c
        wkt = wkt_b.decode('utf-8')

    if not wkt and wkt_version is None:
        # attempt to morph to ESRI before export
        options_wkt[0] = "FORMAT=WKT1_ESRI"
        try:
            exc_wrap_ogrerr(
                OSRExportToWktEx(cogr_srs, &wkt_c, options_wkt)
            )
        except CPLE_BaseError as error:
            gdal_error = error

    if wkt_c != NULL:
        wkt_b = wkt_c
        wkt = wkt_b.decode('utf-8')

    _cpl.CPLFree(wkt_c)

    if not wkt:
        error_message = (
            f"Unable to export CRS to WKT. "
            "Please choose a different WKT version (WKT2 is recommended): "
            "WKT1 | WKT1_GDAL | WKT1_ESRI | WKT2 | WKT2_2018 | WKT2_2015."
        )
        if gdal_error is not None:
            error_message = f"{error_message} GDAL ERROR: {gdal_error}"
        raise CRSError(error_message)
    return wkt


# Export a WKT string from input crs.
def crs_to_wkt(crs, wkt_version=None):
    """Convert a Fiona CRS object to WKT format"""
    cdef OGRSpatialReferenceH cogr_srs = NULL
    cdef char *proj_c = NULL

    try:
        cogr_srs = exc_wrap_pointer(OSRNewSpatialReference(NULL))
    except CPLE_BaseError as exc:
        raise CRSError(str(exc))

    # check for other CRS classes
    if hasattr(crs, "to_wkt") and callable(crs.to_wkt):
        crs = crs.to_wkt()

    # First, check for CRS strings like "EPSG:3857".
    if isinstance(crs, str):
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
    return _osr_to_wkt(cogr_srs, crs, wkt_version)
