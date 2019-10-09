"""Tests of the transform submodule"""

import math

import pytest

from fiona import transform


@pytest.mark.parametrize(
    "geom",
    [
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
    ],
)
def test_transform_geom_with_z(geom):
    """Transforming a geom with Z succeeds"""
    g2 = transform.transform_geom("epsg:4326", "epsg:3857", geom, precision=3)


def test_transform_geom_null_dest():
    failed_geom = {
        'type': 'Polygon',
        'coordinates': ((
            (81.2180196471443, 6.197141424988303),
            (80.34835696810447, 5.968369859232141),
            (79.87246870312859, 6.763463446474915),
            (79.69516686393516, 8.200843410673372),
            (80.14780073437967, 9.824077663609557),
            (80.83881798698664, 9.268426825391174),
            (81.3043192890718, 8.564206244333675),
            (81.78795901889143, 7.523055324733178),
            (81.63732221876066, 6.481775214051936),
            (81.2180196471443, 6.197141424988303)
        ),)
    }
    with pytest.warns(UserWarning):
        assert transform.transform_geom(
            src_crs="epsg:4326",
            dst_crs="epsg:32628",
            geom=failed_geom,
            antimeridian_cutting=True,
            precision=2,
        ) is None
