from .ogrext cimport Session, _deleteOgrFeature
from .ogrext import FIELD_TYPES, FIELD_TYPES_MAP, OGRERR_NONE
from ._shim cimport *
from libc.stdlib cimport malloc, free
from fiona.rfc3339 import FionaDateType, FionaDateTimeType, FionaTimeType

import logging
from six import text_type
import datetime

import numpy as np
cimport numpy as np

log = logging.getLogger(__name__)

def read_vectorized(collection, use_wkb=False):
    cdef Session session
    cdef void * cogr_feature
    cdef void * cogr_geometry
    cdef int num_fields
    cdef void * fdefn
    cdef int feature_index
    cdef int field_index
    cdef char * field_name_c
    cdef bytes field_name_bytes
    cdef int i
    cdef int l
    cdef int y = 0
    cdef int m = 0
    cdef int d = 0
    cdef int hh = 0
    cdef int mm = 0
    cdef int ss = 0
    cdef int tz = 0
    cdef long long fid
    cdef long long [:] arr_int
    cdef double [:] arr_double
    cdef char * wkt
    cdef char * wkb

    session = collection.session
    encoding = session._fileencoding

    if session.cogr_layer == NULL:
        raise ValueError("Null layer")

    length = OGR_L_GetFeatureCount(session.cogr_layer, 0)

    data_fids = np.empty([length], dtype=object)
    data_properties = {}

    if collection.ignore_fields:
        ignore_fields = set(collection.ignore_fields)
    else:
        ignore_fields = set()

    if collection.ignore_geometry:
        ignore_geometry = True
        data_geometry = None
    else:
        ignore_geometry = False
        data_geometry = np.empty([length], dtype=object)

    schema = session.get_schema()
    for field_name, field_type in schema["properties"].items():
        if field_name in ignore_fields:
            continue
        if ":" in field_type:
            field_type, precision = field_type.split(":")
        else:
            precision = None
        if field_type == "int":
            data_properties[field_name] = np.empty([length], dtype=np.int64)
        elif field_type == "float":
            data_properties[field_name] = np.empty([length], dtype=np.float64)
        elif field_type == "str":
            data_properties[field_name] = np.empty([length], dtype=object)
        elif field_type == "bytes":
            data_properties[field_name] = np.empty([length], dtype=object)
        elif field_type == "date":
            data_properties[field_name] = np.empty([length], dtype='datetime64[D]')
        elif field_type == "time":
            # numpy has no dtype for time without date
            data_properties[field_name] = np.empty([length], dtype=object)
        elif field_type == "datetime":
            data_properties[field_name] = np.empty([length], dtype='datetime64[s]')
        else:
            raise TypeError("Unexpected field type: {}".format(field_type))

    OGR_L_ResetReading(session.cogr_layer)
    for feature_index in range(length):
        cogr_feature = OGR_L_GetNextFeature(session.cogr_layer)

        if cogr_feature == NULL:
            raise ValueError("Failed to read feature {}".format(feature_index))

        fid = OGR_F_GetFID(cogr_feature)
        data_fids[feature_index] = str(fid)

        num_fields = OGR_F_GetFieldCount(cogr_feature)
        for field_index in range(num_fields):
            fdefn = OGR_F_GetFieldDefnRef(cogr_feature, field_index)

            # field name
            field_name_c = OGR_Fld_GetNameRef(fdefn)
            field_name_bytes = field_name_c
            field_name = field_name_bytes.decode(encoding)
            if field_name in ignore_fields:
                continue

            # field type
            field_type_id = OGR_Fld_GetType(fdefn)
            field_type_name = FIELD_TYPES[field_type_id]
            field_type = FIELD_TYPES_MAP[field_type_name]

            if field_type is int:
                # TODO: support boolean subtype
                arr_int = data_properties[field_name]
                if is_field_null(cogr_feature, field_index):
                    # TODO: is this the best way to handle NULL values for int?
                    arr_int[feature_index] = 0
                else:
                    arr_int[feature_index] = OGR_F_GetFieldAsInteger64(cogr_feature, field_index)
            elif field_type is float:
                arr_double = data_properties[field_name]
                if is_field_null(cogr_feature, field_index):
                    arr_double[feature_index] = np.nan
                else:
                    arr_double[feature_index] = OGR_F_GetFieldAsDouble(cogr_feature, field_index)
            elif field_type is text_type:
                if is_field_null(cogr_feature, field_index):
                    value = None
                else:
                    try:
                        value = OGR_F_GetFieldAsString(cogr_feature, field_index)
                        value = value.decode(encoding)
                    except UnicodeDecodeError:
                        log.warning(
                            "Failed to decode %s using %s codec", value, encoding)
                arr = data_properties[field_name]
                arr[feature_index] = value
            elif field_type in (FionaDateType, FionaTimeType, FionaDateTimeType):
                arr = data_properties[field_name]
                retval = OGR_F_GetFieldAsDateTime(
                    cogr_feature, field_index, &y, &m, &d, &hh, &mm, &ss, &tz)
                if not retval:
                    arr[feature_index] = None
                else:
                    if field_type is FionaDateType:
                        arr[feature_index] = datetime.date(y, m, d).isoformat()
                    elif field_type is FionaTimeType:
                        arr[feature_index] = datetime.time(hh, mm, ss).isoformat()
                    else:
                        arr[feature_index] = datetime.datetime(y, m, d, hh, mm, ss).isoformat()
            elif field_type is bytes:
                data = OGR_F_GetFieldAsBinary(cogr_feature, field_index, &l)
                arr = data_properties[field_name]
                arr[feature_index] = data[:l]
            else:
                raise TypeError("Unexpected field type: {}".format(field_type))

        if not ignore_geometry:
            cogr_geometry = OGR_F_GetGeometryRef(cogr_feature)
            if cogr_geometry == NULL:
                data_geometry[feature_index] = None
            elif use_wkb:
                length = OGR_G_WkbSize(cogr_geometry)
                wkb = <char*>malloc(sizeof(char)*length)
                result = OGR_G_ExportToWkb(cogr_geometry, 1, wkb)
                if result != OGRERR_NONE:
                    raise ValueError("Failed to export geometry to WKB")
                data_geometry[feature_index] = wkb[:length]
                free(wkb)
            else:
                result = OGR_G_ExportToWkt(cogr_geometry, &wkt)
                if result != OGRERR_NONE:
                    raise ValueError("Failed to export geometry to WKT")
                data_geometry[feature_index] = wkt

        _deleteOgrFeature(cogr_feature)

    features = {
        "id": data_fids,
        "geometry": data_geometry,
        "properties": data_properties,
    }

    return features
