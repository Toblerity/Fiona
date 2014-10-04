"""Raster warping and reprojection"""

from fiona._transform import _transform, _transform_geom


def transform(src_crs, dst_crs, xs, ys):
    """Return transformed vectors of x and y."""
    return _transform(src_crs, dst_crs, xs, ys)


def transform_geom(
        src_crs, dst_crs, geom,
        antimeridian_cutting=False, antimeridian_offset=10.0, precision=-1):
    """Return transformed geometry."""
    return _transform_geom(
        src_crs, dst_crs, geom,
        antimeridian_cutting, antimeridian_offset, precision)
