# distutils: language = c++
#
# Coordinate and geometry transformations.

from __future__ import absolute_import

import logging

from fiona cimport _cpl, _crs, _csl, _geometry
from fiona._crs cimport OGRSpatialReferenceH
from fiona._shim cimport osr_set_traditional_axis_mapping_strategy

from fiona.compat import UserDict


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
    cdef void *src_ogr_geom = NULL
    cdef void *dst_ogr_geom = NULL
    cdef int i

    if src_crs and dst_crs:
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
        src_ogr_geom = _geometry.OGRGeomBuilder().build(geom)
        dst_ogr_geom = factory.transformWithOptions(
                        <const OGRGeometry *>src_ogr_geom,
                        <OGRCoordinateTransformation *>transform,
                        options)
        g = _geometry.GeomBuilder().build(dst_ogr_geom)

        _geometry.OGR_G_DestroyGeometry(dst_ogr_geom)
        _geometry.OGR_G_DestroyGeometry(src_ogr_geom)
        _crs.OCTDestroyCoordinateTransformation(transform)
        if options != NULL:
            _csl.CSLDestroy(options)
        _crs.OSRRelease(src)
        _crs.OSRRelease(dst)

    else:
        g = geom

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
            for piece in g['coordinates']:
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
        
        if g['type'] == 'GeometryCollection':
            for _g in g['geometries']:
                round_geometry(_g)
        else:
            round_geometry(g)

    return g
