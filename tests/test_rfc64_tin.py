"""Tests of features related to GDAL RFC 64

See https://trac.osgeo.org/gdal/wiki/rfc64_triangle_polyhedralsurface_tin.
"""

import fiona

from .conftest import requires_gdal22


def test_tin_shp(path_test_tin_shp):
    """Convert TIN to MultiPolygon"""
    with fiona.open(path_test_tin_shp) as col:
        assert col.schema['geometry'] == 'Unknown'
        features = list(col)
        assert len(features) == 1
        assert features[0]['geometry']['type'] == 'MultiPolygon'
        assert features[0]['geometry']['coordinates'] == [[[(0.0, 0.0, 0.0),
                                                            (0.0, 0.0, 1.0),
                                                            (0.0, 1.0, 0.0),
                                                            (0.0, 0.0, 0.0)]],
                                                          [[(0.0, 0.0, 0.0),
                                                            (0.0, 1.0, 0.0),
                                                            (1.0, 1.0, 0.0),
                                                            (0.0, 0.0, 0.0)]]]


@requires_gdal22
def test_tin_csv(path_test_tin_csv):
    """Convert TIN to MultiPolygon and Triangle to Polygon"""
    with fiona.open(path_test_tin_csv) as col:
        assert col.schema['geometry'] == 'Unknown'
        features = list(col)
        assert len(features) == 2
        assert features[0]['geometry']['type'] == 'MultiPolygon'
        assert features[0]['geometry']['coordinates'] == [[[(0.0, 0.0, 0.0),
                                                            (0.0, 0.0, 1.0),
                                                            (0.0, 1.0, 0.0),
                                                            (0.0, 0.0, 0.0)]],
                                                          [[(0.0, 0.0, 0.0),
                                                              (0.0, 1.0, 0.0),
                                                              (1.0, 1.0, 0.0),
                                                              (0.0, 0.0, 0.0)]]]

        assert features[1]['geometry']['type'] == 'Polygon'
        assert features[1]['geometry']['coordinates'] == [[(0.0, 0.0, 0.0),
                                                           (0.0, 1.0, 0.0),
                                                           (1.0, 1.0, 0.0),
                                                           (0.0, 0.0, 0.0)]]
