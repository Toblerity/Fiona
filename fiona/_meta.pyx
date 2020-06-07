
include "gdal.pxi"

from fiona._err cimport  exc_wrap_pointer
from fiona.compat import strencode
from fiona._shim cimport gdal_open_vector
from fiona.env import require_gdal_version
import logging

# This is required otherwise GDALGetDriverByName returns NULL for GDAL 1.x
from fiona._shim cimport *


log = logging.getLogger(__name__)


@require_gdal_version('2.0')
def _get_metadata_item(driver, metadata_item):
    """Query metadata items

    Parameters
    ----------
    driver : str
        Driver to query
    metadata_item : str
        Metadata item to query

    Returns
    -------
    str
        XML of metadata item or empty string

    """
    cdef char* metadata_c = NULL
    cdef void *cogr_driver

    cogr_driver = exc_wrap_pointer(GDALGetDriverByName(driver.encode('utf-8')))
    metadata_c = GDALGetMetadataItem(cogr_driver, strencode(metadata_item), NULL)

    metadata = None
    if metadata_c != NULL:
        metadata = metadata_c
        metadata = metadata.decode('utf-8')

        if len(metadata) == 0:
            metadata = None

    return metadata
