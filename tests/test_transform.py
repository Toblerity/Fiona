"""Tests of the transform submodule"""

import math
import pytest
from fiona import transform

from .conftest import requires_gdal_lt_3


TEST_GEOMS = [
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


@pytest.mark.parametrize("geom", TEST_GEOMS)
def test_transform_geom_with_z(geom):
    """Transforming a geom with Z succeeds"""
    transform.transform_geom("epsg:4326", "epsg:3857", geom, precision=3)


@pytest.mark.parametrize("geom", TEST_GEOMS)
def test_transform_geom_array_z(geom):
    """Transforming a geom array with Z succeeds"""
    g2 = transform.transform_geom(
        "epsg:4326",
        "epsg:3857",
        [geom for _ in range(5)],
        precision=3,
    )
    assert isinstance(g2, list)
    assert len(g2) == 5


@requires_gdal_lt_3
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
        transformed_geom = transform.transform_geom(
            src_crs="epsg:4326",
            dst_crs="epsg:32628",
            geom=failed_geom,
            antimeridian_cutting=True,
            precision=2,
        )
        assert transformed_geom is None


@pytest.mark.parametrize("crs", ["epsg:4326",
                                 "EPSG:4326",
                                 "WGS84",
                                 {'init': 'epsg:4326'},
                                 {'proj': 'longlat', 'datum': 'WGS84', 'no_defs': True},
                                 "OGC:CRS84"])
def test_axis_ordering(crs):
    """ Test if transform uses traditional_axis_mapping """

    expected = (-8427998.647958742, 4587905.27136252)
    t1 = transform.transform(crs, "epsg:3857", [-75.71], [38.06])
    assert (t1[0][0], t1[1][0]) == pytest.approx(expected)
    geom = {"type": "Point", "coordinates": [-75.71, 38.06]}
    g1 = transform.transform_geom(crs, "epsg:3857", geom, precision=3)
    assert g1["coordinates"] == pytest.approx(expected)

    rev_expected = (-75.71, 38.06)
    t2 = transform.transform("epsg:3857", crs, [-8427998.647958742], [4587905.27136252])
    assert (t2[0][0], t2[1][0]) == pytest.approx(rev_expected)
    geom = {"type": "Point", "coordinates": [-8427998.647958742, 4587905.27136252]}
    g2 = transform.transform_geom("epsg:3857", crs, geom, precision=3)
    assert g2["coordinates"] == pytest.approx(rev_expected)
