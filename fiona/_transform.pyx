# distutils: language = c++
#
# Coordinate and geometry transformations.

from __future__ import absolute_import

import logging
import warnings

from fiona cimport _cpl, _crs, _csl, _geometry
from fiona._crs cimport OGRSpatialReferenceH
from fiona._shim cimport osr_set_traditional_axis_mapping_strategy

from fiona.compat import UserDict, DICT_TYPES


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
    cdef char *proj_c = NULL
    cdef OGRSpatialReferenceH osr = NULL
    osr = _crs.OSRNewSpatialReference(NULL)
    if osr == NULL:
        raise ValueError("NULL spatial reference")
    params = []
    # Normally, we expect a CRS dict.
    if isinstance(crs, UserDict):
        crs = dict(crs)

    if isinstance(crs, dict):
        # EPSG is a special case.
        init = crs.get('init')
        if init:
            auth, val = init.split(':')
            if auth.upper() == 'EPSG':
                _crs.OSRImportFromEPSG(osr, int(val))
        else:
            crs['wktext'] = True
            for k, v in crs.items():
                if v is True or (k in ('no_defs', 'wktext') and v):
                    params.append("+%s" % k)
                else:
                    params.append("+%s=%s" % (k, v))
            proj = " ".join(params)
            log.debug("PROJ.4 to be imported: %r", proj)
            proj_b = proj.encode('utf-8')
            proj_c = proj_b
            _crs.OSRImportFromProj4(osr, proj_c)
    # Fall back for CRS strings like "EPSG:3857."
    else:
        proj_b = crs.encode('utf-8')
        proj_c = proj_b
        _crs.OSRSetFromUserInput(osr, proj_c)

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

    transform = _crs.OCTNewCoordinateTransformation(src, dst)
    res = _crs.OCTTransform(transform, n, x, y, NULL)

    res_xs = [0]*n
    res_ys = [0]*n

    for i in range(n):
        res_xs[i] = x[i]
        res_ys[i] = y[i]

    _cpl.CPLFree(x)
    _cpl.CPLFree(y)
    _crs.OCTDestroyCoordinateTransformation(transform)
    _crs.OSRRelease(src)
    _crs.OSRRelease(dst)
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
    src_ogr_geom = _geometry.OGRGeomBuilder().build(single_geom)
    dst_ogr_geom = factory.transformWithOptions(
                    <const OGRGeometry *>src_ogr_geom,
                    <OGRCoordinateTransformation *>transform,
                    options)
    if dst_ogr_geom == NULL:
        out_geom = None
        warnings.warn(
            "Full reprojection failed, but partial is possible. To enable partial "
            "reprojection wrap the transform_geom call like so:\n"
            "with fiona.Env(OGR_ENABLE_PARTIAL_REPROJECTION=True):\n"
            "    transform_geom(...)"
        )
    else:
        out_geom = _geometry.GeomBuilder().build(dst_ogr_geom)
        _geometry.OGR_G_DestroyGeometry(dst_ogr_geom)
    if src_ogr_geom != NULL:
        _geometry.OGR_G_DestroyGeometry(src_ogr_geom)

    if out_geom is not None and precision >= 0:
        if out_geom['type'] == 'Point':
            coords = list(out_geom['coordinates'])
            x, y = coords[:2]
            x = round(x, precision)
            y = round(y, precision)
            new_coords = [x, y]
            if len(coords) == 3:
                z = coords[2]
                new_coords.append(round(z, precision))

        elif out_geom['type'] in ['LineString', 'MultiPoint']:
            coords = list(zip(*out_geom['coordinates']))
            xp, yp = coords[:2]
            xp = [round(v, precision) for v in xp]
            yp = [round(v, precision) for v in yp]
            if len(coords) == 3:
                zp = coords[2]
                zp = [round(v, precision) for v in zp]
                new_coords = list(zip(xp, yp, zp))
            else:
                new_coords = list(zip(xp, yp))

        elif out_geom['type'] in ['Polygon', 'MultiLineString']:
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

        elif out_geom['type'] == 'MultiPolygon':
            parts = out_geom['coordinates']
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

        out_geom['coordinates'] = new_coords
    return out_geom


def _transform_geom(
        src_crs, dst_crs, geom, antimeridian_cutting, antimeridian_offset,
        precision):
    """Return a transformed geometry."""
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
    transform = _crs.OCTNewCoordinateTransformation(src, dst)
    # Transform options.
    options = _csl.CSLSetNameValue(
                options, "DATELINEOFFSET", 
                str(antimeridian_offset).encode('utf-8'))
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

    _crs.OCTDestroyCoordinateTransformation(transform)
    if options != NULL:
        _csl.CSLDestroy(options)
    _crs.OSRRelease(src)
    _crs.OSRRelease(dst)
    return out_geom