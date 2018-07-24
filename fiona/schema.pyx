from six import text_type

from fiona.errors import SchemaError
from fiona.rfc3339 import FionaDateType, FionaDateTimeType, FionaTimeType


cdef extern from "gdal.h":
    char * GDALVersionInfo (char *pszRequest)


def _get_gdal_version_num():
    """Return current internal version number of gdal"""
    return int(GDALVersionInfo("VERSION_NUM"))


GDAL_VERSION_NUM = _get_gdal_version_num()

# Mapping of OGR integer field types to Fiona field type names.
# Lists are currently unsupported in this version, but might be done as
# arrays in a future version.
FIELD_TYPES = [
    'int32',        # OFTInteger, Simple 32bit integer
    None,           # OFTIntegerList, List of 32bit integers
    'float',        # OFTReal, Double Precision floating point
    None,           # OFTRealList, List of doubles
    'str',          # OFTString, String of UTF-8 chars
    None,           # OFTStringList, Array of strings
    None,           # OFTWideString, deprecated
    None,           # OFTWideStringList, deprecated
    'bytes',        # OFTBinary, Raw Binary data
    'date',         # OFTDate, Date
    'time',         # OFTTime, Time
    'datetime',     # OFTDateTime, Date and Time
    'int64',        # OFTInteger64, Single 64bit integer
    None            # OFTInteger64List, List of 64bit integers
]

# Mapping of Fiona field type names to Python types.
FIELD_TYPES_MAP = {
    'int32': int,
    'float': float,
    'str': text_type,
    'date': FionaDateType,
    'time': FionaTimeType,
    'datetime': FionaDateTimeType,
    'bytes': bytes,
    'int64': int,
    'int': int
}

FIELD_TYPES_MAP_REV = dict([(v, k) for k, v in FIELD_TYPES_MAP.items()])
FIELD_TYPES_MAP_REV[int] = 'int'


def normalize_field_type(ftype):
    """Normalize free form field types to an element of FIELD_TYPES

    Parameters
    ----------
    ftype : str
        A type:width format like 'int:9' or 'str:255'

    Returns
    -------
    str
        An element from FIELD_TYPES
    """
    if ftype in FIELD_TYPES:
        return ftype
    elif ftype == 'bool':
        return 'bool'
    elif ftype.startswith('int'):
        width = int((ftype.split(':')[1:] or ['0'])[0])
        if GDAL_VERSION_NUM >= 2000000 and (width == 0 or width >= 10):
            return 'int64'
        else:
            return 'int32'
    elif ftype.startswith('str'):
        return 'str'
    elif ftype.startswith('float'):
        return 'float'
    else:
        raise SchemaError("Unknown field type: {}".format(ftype))
