"""Fiona schema module."""

include "gdal.pxi"

import itertools
from typing import List

from fiona.errors import SchemaError
from fiona.rfc3339 import FionaDateType, FionaDateTimeType, FionaTimeType


def _get_gdal_version_num():
    """Return current internal version number of gdal"""
    return int(GDALVersionInfo("VERSION_NUM"))


class FionaIntegerType:
    names = ["int32"]
    type = int


class FionaInt16Type:
    names = ["int16"]
    type = int


class FionaBooleanType:
    names = ["bool"]
    type = bool


class FionaInteger64Type:
    names = ["int", "int64"]
    type = int


class FionaRealType:
    names = ["float", "float64"]
    type = float


class FionaStringType:
    names = ["str"]
    type = str


class FionaBinaryType:
    names = ["bytes"]
    type = bytes


class FionaStringListType:
    names = ["List[str]", "list[str]"]
    type = List[str]


class FionaJSONType:
    names = ["json"]
    type = str


# Mapping of OGR integer field types to Fiona field type names.
# Lists are currently unsupported in this version, but might be done as
# arrays in a future version.
FIELD_TYPES = [
    'int32',        # OFTInteger, Simple 32bit integer
    None,           # OFTIntegerList, List of 32bit integers
    'float',        # OFTReal, Double Precision floating point
    None,           # OFTRealList, List of doubles
    'str',          # OFTString, String of UTF-8 chars
    'List[str]',    # OFTStringList, Array of strings
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
    'str': str,
    'date': FionaDateType,
    'time': FionaTimeType,
    'datetime': FionaDateTimeType,
    'bytes': bytes,
    'int64': int,
    'int': int,
    'List[str]': List[str],
}

FIELD_TYPES_MAP_REV = dict([(v, k) for k, v in FIELD_TYPES_MAP.items()])
FIELD_TYPES_MAP_REV[int] = 'int'


FIELD_TYPES_MAP2_REV = {
    (OFTInteger, OFSTNone): FionaIntegerType,
    (OFTInteger, OFSTBoolean): FionaBooleanType,
    (OFTInteger, OFSTInt16): FionaInt16Type,
    (OFTInteger64, OFSTNone): FionaInteger64Type,
    (OFTReal, OFSTNone): FionaRealType,
    (OFTString, OFSTNone): FionaStringType,
    (OFTDate, OFSTNone): FionaDateType,
    (OFTTime, OFSTNone): FionaTimeType,
    (OFTDateTime, OFSTNone): FionaDateTimeType,
    (OFTBinary, OFSTNone): FionaBinaryType,
    (OFTStringList, OFSTNone): FionaStringListType,
    (OFTString, OFSTJSON): FionaJSONType,
}
FIELD_TYPES_MAP2 = {v: k for k, v in FIELD_TYPES_MAP2_REV.items()}
FIELD_TYPES_NAMES = list(itertools.chain.from_iterable((k.names for k in FIELD_TYPES_MAP2)))
NAMED_FIELD_TYPES = {n: k for k in FIELD_TYPES_MAP2 for n in k.names}


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
    if ftype in FIELD_TYPES_NAMES:
        return ftype
    elif ftype.startswith('int'):
        width = int((ftype.split(':')[1:] or ['0'])[0])
        if width == 0 or width >= 10:
            return 'int64'
        else:
            return 'int32'
    elif ftype.startswith('str'):
        return 'str'
    elif ftype.startswith('float'):
        return 'float'
    else:
        raise SchemaError(f"Unknown field type: {ftype}")
