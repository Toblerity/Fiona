"""Tests of the transform submodule"""

import math

import pytest

from fiona import transform
from fiona._geometry import geometry_as_wkb

params = [
    {"type": "Point", "coordinates": [0.0, 0.0, 1000.0]},
    {
        "type": "LineString",
        "coordinates": [[0.0, 0.0, 1000.0], [0.1, 0.1, -1000.0]],
    },
    {
        "type": "MultiPoint",
        "coordinates": [[0.0, 0.0, 1000.0], [0.1, 0.1, -1000.0]],
    },
    {
        "type": "Polygon",
        "coordinates": [
            [
                [0.0, 0.0, 1000.0],
                [0.1, 0.1, -1000.0],
                [0.1, -0.1, math.pi],
                [0.0, 0.0, 1000.0],
            ]
        ],
    },
    {
        "type": "MultiPolygon",
        "coordinates": [
            [
                [
                    [0.0, 0.0, 1000.0],
                    [0.1, 0.1, -1000.0],
                    [0.1, -0.1, math.pi],
                    [0.0, 0.0, 1000.0],
                ]
            ]
        ],
    },
]


@pytest.mark.parametrize("geom", params)
def test_transform_geom_with_z(geom):
    """Transforming a geom with Z succeeds"""
    g2 = transform.transform_geom("epsg:4326", "epsg:3857", geom, precision=3)


@pytest.mark.parametrize("geom", params)
def test_transform_wkb(geom):
    """Transforming a geom with Z succeeds"""
    wkb = geometry_as_wkb(geom)
    g2 = transform.transform_wkb("epsg:4326", "epsg:3857", wkb)
