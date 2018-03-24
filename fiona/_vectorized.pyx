from .ogrext cimport Session, _deleteOgrFeature
from .ogrext import FIELD_TYPES, FIELD_TYPES_MAP, OGRERR_NONE
from ._shim cimport *

import logging
from six import text_type

import numpy as np
cimport numpy as np

log = logging.getLogger(__name__)

def read_vectorized(collection):
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
    cdef long long [:] arr_int
    cdef double [:] arr_double
    cdef char * wkt

    session = collection.session
    encoding = session._fileencoding

    if session.cogr_layer == NULL:
        raise ValueError("Null layer")

    length = OGR_L_GetFeatureCount(session.cogr_layer, 0)

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
        field_type, precision = field_type.split(":")
        if field_type == "int":
            data_properties[field_name] = np.empty([length], dtype=np.int64)
        elif field_type == "float":
            data_properties[field_name] = np.empty([length], dtype=np.float64)
        elif field_type == "str":
            data_properties[field_name] = np.empty([length], dtype=object)
        else:
            # TODO: other types (dates, bytes, boolean subtype)
            raise TypeError("Unexpected field type: {}".format(field_type))

    for feature_index in range(length):
        # TODO: this isn't the correct way to iterate over features
        cogr_feature = OGR_L_GetFeature(session.cogr_layer, feature_index)

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
                arr_int = data_properties[field_name]
                if is_field_null(cogr_feature, field_index):
                    # TODO: this isn't the correct way to handle NULL for ints
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
            else:
                raise TypeError("Unexpected field type: {}".format(field_type))

        if not ignore_geometry:
            cogr_geometry = OGR_F_GetGeometryRef(cogr_feature)
            if cogr_geometry == NULL:
                data_geometry[feature_index] = None
            else:
                result = OGR_G_ExportToWkt(cogr_geometry, &wkt)
                if result != OGRERR_NONE:
                    raise ValueError("Failed to export geometry to WKT")
                data_geometry[feature_index] = wkt

        _deleteOgrFeature(cogr_feature)

    features = {
        "geometry": data_geometry,
        "properties": data_properties,
    }

    return features
