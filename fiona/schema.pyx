"""Fiona schema module."""

include "gdal.pxi"

import itertools
from typing import List

from fiona.errors import SchemaError


def _get_gdal_version_num():
    """Return current internal version number of gdal"""
    return int(GDALVersionInfo("VERSION_NUM"))


cdef class AbstractFieldType:
    pass


cdef class FionaIntegerType(AbstractFieldType):
    names = ["int32"]
    type = int


cdef class FionaInt16Type(AbstractFieldType):
    names = ["int16"]
    type = int


cdef class FionaBooleanType(AbstractFieldType):
    names = ["bool"]
    type = bool


cdef class FionaInteger64Type(AbstractFieldType):
    names = ["int", "int64"]
    type = int


cdef class FionaRealType(AbstractFieldType):
    names = ["float", "float64"]
    type = float


cdef class FionaStringType(AbstractFieldType):
    names = ["str"]
    type = str


cdef class FionaBinaryType(AbstractFieldType):
    names = ["bytes"]
    type = bytes


cdef class FionaStringListType(AbstractFieldType):
    names = ["List[str]", "list[str]"]
    type = List[str]


cdef class FionaJSONType(AbstractFieldType):
    names = ["json"]
    type = str


cdef class FionaDateType(AbstractFieldType):
    """Dates without time."""
    names = ["date"]
    type = str


cdef class FionaTimeType(AbstractFieldType):
    """Times without dates."""
    names = ["time"]
    type = str


cdef class FionaDateTimeType(AbstractFieldType):
    """Dates and times."""
    names = ["datetime"]
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
