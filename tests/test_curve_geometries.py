"""Tests of features related to GDAL RFC 49

See https://trac.osgeo.org/gdal/wiki/rfc49_curve_geometries.
"""

import fiona

from .conftest import requires_gdal2


@requires_gdal2
def test_line_curve_conversion(path_curves_line_csv):
    """Convert curved geometries to linear approximations"""
    with fiona.open(path_curves_line_csv) as col:
        assert col.schema['geometry'] == 'Unknown'
        features = list(col)
        assert len(features) == 9
