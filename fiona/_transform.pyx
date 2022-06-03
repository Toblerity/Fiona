# distutils: language = c++
#
# Coordinate and geometry transformations.
from __future__ import absolute_import

include "gdal.pxi"

import logging
import warnings
from collections import UserDict

from fiona cimport _cpl, _csl, _geometry
from fiona.crs cimport OGRSpatialReferenceH, osr_set_traditional_axis_mapping_strategy
from fiona._err cimport exc_wrap_pointer

from fiona.compat import DICT_TYPES
from fiona.crs import CRS
from fiona.model import Geometry


cdef extern from "ogr_geometry.h" nogil:

    cdef cppclass OGRGeometry:
        pass

    cdef cppclass OGRGeometryFactory:
        void * transformWithOptions(void *geom, void *ct, char **options)


cdef extern from "ogr_spatialref.h":

    cdef cppclass OGRCoordinateTransformation:
        pass


log = logging.getLogger(__name__)
class NullHandler(logging.Handler):
    def emit(self, record):
        pass
log.addHandler(NullHandler())


cdef void *_crs_from_crs(object crs):
    cdef char *wkt_c = NULL
    cdef OGRSpatialReferenceH osr = NULL
    osr = OSRNewSpatialReference(NULL)

    if osr == NULL:
        raise ValueError("NULL spatial reference")

    params = []

    wkt = CRS.from_user_input(crs).to_wkt()

    wkt_b = wkt.encode('utf-8')
    wkt_c = wkt_b
    OSRSetFromUserInput(osr, wkt_c)

    osr_set_traditional_axis_mapping_strategy(osr)
    return osr


def _transform(src_crs, dst_crs, xs, ys):
    cdef double *x
    cdef double *y
    cdef char *proj_c = NULL
    cdef OGRSpatialReferenceH src = NULL
    cdef OGRSpatialReferenceH dst = NULL
    cdef void *transform = NULL
    cdef int i

    assert len(xs) == len(ys)

    src = _crs_from_crs(src_crs)
    dst = _crs_from_crs(dst_crs)

    n = len(xs)
    x = <double *>_cpl.CPLMalloc(n*sizeof(double))
    y = <double *>_cpl.CPLMalloc(n*sizeof(double))
    for i in range(n):
        x[i] = xs[i]
        y[i] = ys[i]

    transform = OCTNewCoordinateTransformation(src, dst)
    res = OCTTransform(transform, n, x, y, NULL)

    res_xs = [0]*n
    res_ys = [0]*n

    for i in range(n):
        res_xs[i] = x[i]
        res_ys[i] = y[i]

    _cpl.CPLFree(x)
    _cpl.CPLFree(y)
    OCTDestroyCoordinateTransformation(transform)
    OSRRelease(src)
    OSRRelease(dst)
    return res_xs, res_ys


cdef object _transform_single_geom(
    object single_geom,
    OGRGeometryFactory *factory,
    void *transform,
    char **options,
    object precision
):
    cdef void *src_ogr_geom = NULL
    cdef void *dst_ogr_geom = NULL
    cdef int i

    if not isinstance(single_geom, Geometry):
        single_geom = Geometry.from_dict(**single_geom)

    src_ogr_geom = _geometry.OGRGeomBuilder().build(single_geom)
    dst_ogr_geom = factory.transformWithOptions(
                    <const OGRGeometry *>src_ogr_geom,
                    <OGRCoordinateTransformation *>transform,
                    options)

    if dst_ogr_geom == NULL:
        warnings.warn(
            "Full reprojection failed, but partial is possible. To enable partial "
            "reprojection wrap the transform_geom call like so:\n"
            "with fiona.Env(OGR_ENABLE_PARTIAL_REPROJECTION=True):\n"
            "    transform_geom(...)"
        )
        return None
    else:
        out_geom = _geometry.GeomBuilder().build(dst_ogr_geom)
        _geometry.OGR_G_DestroyGeometry(dst_ogr_geom)

    if src_ogr_geom != NULL:
        _geometry.OGR_G_DestroyGeometry(src_ogr_geom)

    if precision >= 0:

        def round_point(g):
            coords = list(g['coordinates'])
            x, y = coords[:2]
            x = round(x, precision)
            y = round(y, precision)
            new_coords = [x, y]
            if len(coords) == 3:
                z = coords[2]
                new_coords.append(round(z, precision))
            return new_coords

        def round_linestring(g):
            coords = list(zip(*g['coordinates']))
            xp, yp = coords[:2]
            xp = [round(v, precision) for v in xp]
            yp = [round(v, precision) for v in yp]
            if len(coords) == 3:
                zp = coords[2]
                zp = [round(v, precision) for v in zp]
                new_coords = list(zip(xp, yp, zp))
            else:
                new_coords = list(zip(xp, yp))
            return new_coords

        def round_polygon(g):
            new_coords = []
            for piece in out_geom['coordinates']:
                coords = list(zip(*piece))
                xp, yp = coords[:2]
                xp = [round(v, precision) for v in xp]
                yp = [round(v, precision) for v in yp]
                if len(coords) == 3:
                    zp = coords[2]
                    zp = [round(v, precision) for v in zp]
                    new_coords.append(list(zip(xp, yp, zp)))
                else:
                    new_coords.append(list(zip(xp, yp)))
            return new_coords

        def round_multipolygon(g):
            parts = g['coordinates']
            new_coords = []
            for part in parts:
                inner_coords = []
                for ring in part:
                    coords = list(zip(*ring))
                    xp, yp = coords[:2]
                    xp = [round(v, precision) for v in xp]
                    yp = [round(v, precision) for v in yp]
                    if len(coords) == 3:
                        zp = coords[2]
                        zp = [round(v, precision) for v in zp]
                        inner_coords.append(list(zip(xp, yp, zp)))
                    else:
                        inner_coords.append(list(zip(xp, yp)))
                new_coords.append(inner_coords)
            return new_coords

        def round_geometry(g):
            if g['type'] == 'Point':
                g['coordinates'] = round_point(g)
            elif g['type'] in ['LineString', 'MultiPoint']:
                g['coordinates'] = round_linestring(g)
            elif g['type'] in ['Polygon', 'MultiLineString']:
                g['coordinates'] = round_polygon(g)
            elif g['type'] == 'MultiPolygon':
                g['coordinates'] = round_multipolygon(g)
            else:
                raise RuntimeError("Unsupported geometry type: {}".format(g['type']))

        if out_geom['type'] == 'GeometryCollection':
            for _g in out_geom['geometries']:
                round_geometry(_g)
        else:
            round_geometry(out_geom)

    return out_geom


def _transform_geom(src_crs, dst_crs, geom, antimeridian_cutting, antimeridian_offset, precision):
    """Return a transformed geometry.

    """
    cdef char *proj_c = NULL
    cdef char *key_c = NULL
    cdef char *val_c = NULL
    cdef char **options = NULL
    cdef OGRSpatialReferenceH src = NULL
    cdef OGRSpatialReferenceH dst = NULL
    cdef void *transform = NULL
    cdef OGRGeometryFactory *factory = NULL

    if not all([src_crs, dst_crs]):
        raise RuntimeError("Must provide a source and destination CRS.")

    src = _crs_from_crs(src_crs)
    dst = _crs_from_crs(dst_crs)
    transform = OCTNewCoordinateTransformation(src, dst)

    # Transform options.
    options = _csl.CSLSetNameValue(
        options,
        "DATELINEOFFSET",
        str(antimeridian_offset).encode('utf-8')
    )

    if antimeridian_cutting:
        options = _csl.CSLSetNameValue(options, "WRAPDATELINE", "YES")

    factory = new OGRGeometryFactory()

    if isinstance(geom, DICT_TYPES):
        out_geom = _transform_single_geom(geom, factory, transform, options, precision)
    else:
        out_geom = [
            _transform_single_geom(single_geom, factory, transform, options, precision)
            for single_geom in geom
        ]

    OCTDestroyCoordinateTransformation(transform)

    if options != NULL:
        _csl.CSLDestroy(options)

    OSRRelease(src)
    OSRRelease(dst)

    return out_geom


from libcpp.unordered_map cimport unordered_map

cdef OGRGeometryH segmentize(OGRGeometryH geom, double max_length):
    cdef OGRGeometryH new_geom = NULL
    new_geom = OGR_G_Clone(geom)
    OGR_G_Segmentize(new_geom, max_length)
    return new_geom


ctypedef OGRGeometryH (*geometry_func)(OGRGeometryH, double)
cdef unordered_map[int, geometry_func] func_map

func_map[1] = <geometry_func>segmentize

cdef geometry_func func_alias(int choice):
    return func_map[choice]


def apply_geom(operations, geoms):
    """Apply a series of geometry transforming operations to one or more geometries.

    Parameters
    ----------
    operations: list
        A list of operation names and extra arg as a tuple.
    geoms: Geometry or Sequence[Geometry]
        Geometries on which to apply operations.

    Yields
    ------
    Geometry

    """
    cdef OGRGeometryH ogr_geom1 = NULL
    cdef OGRGeometryH ogr_geom2 = NULL
    cdef int choice = 0

    op_map = {
        "segmentize": 1
    }

    for geom in geoms:
        ogr_geom1 = _geometry.OGRGeomBuilder().build(geom)

        for op_name, op_arg in operations:
            choice = op_map[op_name]
            ogr_geom2 = func_alias(choice)(ogr_geom1, op_arg)
            ogr_geom2 = exc_wrap_pointer(ogr_geom2)
            OGR_G_DestroyGeometry(ogr_geom1)
            ogr_geom1 = ogr_geom2

        if ogr_geom2 == NULL:
            raise Exception("NULL geometry")

        output_geom = _geometry.GeomBuilder().build(ogr_geom2)
        OGR_G_DestroyGeometry(ogr_geom2)

        yield output_geom
