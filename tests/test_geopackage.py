import os
import pytest
import fiona
from fiona.model import Feature

from .conftest import requires_gpkg

example_schema = {
    "geometry": "Point",
    "properties": [("title", "str")],
}

example_crs = {
    "a": 6370997,
    "lon_0": -100,
    "y_0": 0,
    "no_defs": True,
    "proj": "laea",
    "x_0": 0,
    "units": "m",
    "b": 6370997,
    "lat_0": 45,
}

example_features = [
    Feature.from_dict(
        **{
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"title": "One"},
        }
    ),
    Feature.from_dict(
        **{
            "geometry": {"type": "Point", "coordinates": [1.0, 2.0]},
            "properties": {"title": "Two"},
        }
    ),
    Feature.from_dict(
        **{
            "geometry": {"type": "Point", "coordinates": [3.0, 4.0]},
            "properties": {"title": "Three"},
        }
    ),
]


@requires_gpkg
def test_read_gpkg(path_coutwildrnp_gpkg):
    """
    Implicitly tests writing gpkg as the fixture will create the data source on
    first request
    """
    with fiona.open(path_coutwildrnp_gpkg, "r") as src:
        assert len(src) == 67
        feature = next(iter(src))
        assert feature.geometry["type"] == "Polygon"
        assert feature.properties["NAME"] == "Mount Naomi Wilderness"


@requires_gpkg
def test_write_gpkg(tmpdir):
    path = str(tmpdir.join("foo.gpkg"))

    with fiona.open(
        path, "w", driver="GPKG", schema=example_schema, crs=example_crs
    ) as dst:
        dst.writerecords(example_features)

    with fiona.open(path) as src:
        assert src.schema["geometry"] == "Point"
        assert len(src) == 3


@requires_gpkg
def test_write_multilayer_gpkg(tmpdir):
    """
    Test that writing a second layer to an existing geopackage doesn't remove
    and existing layer for the dataset.
    """
    path = str(tmpdir.join("foo.gpkg"))

    with fiona.open(
        path, "w", driver="GPKG", schema=example_schema, layer="layer1", crs=example_crs
    ) as dst:
        dst.writerecords(example_features[0:2])

    with fiona.open(
        path, "w", driver="GPKG", schema=example_schema, layer="layer2", crs=example_crs
    ) as dst:
        dst.writerecords(example_features[2:])

    with fiona.open(path, layer="layer1") as src:
        assert src.schema["geometry"] == "Point"
        assert len(src) == 2

    with fiona.open(path, layer="layer2") as src:
        assert src.schema["geometry"] == "Point"
        assert len(src) == 1


@requires_gpkg
def test_gpkg_index_starts_at_one(path_coutwildrnp_gpkg):
    """GeoPackage feature ids start at 1, see issue #1187."""
    with fiona.open(path_coutwildrnp_gpkg) as src:
        assert src[0] is None
        assert src[1].id == "1"
        assert src[len(src)].id == "67"


@requires_gpkg
def test_gpkg_first_and_last_by_iteration(path_coutwildrnp_gpkg):
    """Iteration gives the first and last features, as shown in the manual."""
    from collections import deque

    with fiona.open(path_coutwildrnp_gpkg) as src:
        first = next(iter(src))
        last = deque(src, maxlen=1)[0]
        assert first.id == "1"
        assert last.id == "67"
        assert last.properties == src[len(src)].properties
