"""Tests of features related to GDAL RFC 64

See https://trac.osgeo.org/gdal/wiki/rfc64_triangle_polyhedralsurface_tin.
"""

import fiona

from .conftest import requires_gdal22


def test_tin_shp(path_test_tin_shp):
    """Convert TIN to MultiPolygon"""
    with fiona.open(path_test_tin_shp) as col:
        assert col.schema["geometry"] == "Unknown"
        features = list(col)
        assert len(features) == 1
        assert features[0]["geometry"]["type"] == "MultiPolygon"
        assert features[0]["geometry"]["coordinates"] == [
            [[(0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0)]],
            [[(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (0.0, 0.0, 0.0)]],
        ]


@requires_gdal22
def test_tin_csv(path_test_tin_csv):
    """Convert TIN to MultiPolygon and Triangle to Polygon"""
    with fiona.open(path_test_tin_csv) as col:
        assert col.schema["geometry"] == "Unknown"

        feature1 = next(col)
        # features = list(col)
        # assert len(features) == 3
        assert feature1["geometry"]["type"] == "MultiPolygon"
        assert feature1["geometry"]["coordinates"] == [
            [[(0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0)]],
            [[(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (0.0, 0.0, 0.0)]],
        ]

        feature2 = next(col)
        assert feature2["geometry"]["type"] == "Polygon"
        assert feature2["geometry"]["coordinates"] == [
            [(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (0.0, 0.0, 0.0)]
        ]

        feature3 = next(col)
        assert feature3["geometry"]["type"] == "GeometryCollection"
        assert len(feature3["geometry"]["geometries"]) == 2
        assert feature3["geometry"]["geometries"][0]["type"] == "MultiPolygon"
        assert feature3["geometry"]["geometries"][0]["coordinates"] == [
            [[(0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (0.0, 1.0, 0.0), (0.0, 0.0, 0.0)]],
            [[(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (0.0, 0.0, 0.0)]],
        ]

        assert feature3["geometry"]["geometries"][1]["type"] == "Polygon"
        assert feature3["geometry"]["geometries"][1]["coordinates"] == [
            [(0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0), (0.0, 0.0, 0.0)]
        ]
