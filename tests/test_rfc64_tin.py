"""Tests of features related to GDAL RFC 64

See https://trac.osgeo.org/gdal/wiki/rfc64_triangle_polyhedralsurface_tin.
"""

import fiona

from .conftest import requires_gdal2


@requires_gdal2
def test_tin(path_test_tin):
    """Convert curved geometries to linear approximations"""
    with fiona.open(path_test_tin) as col:
        assert col.schema['geometry'] == 'Unknown'
        features = list(col)
        assert len(features) == 2
