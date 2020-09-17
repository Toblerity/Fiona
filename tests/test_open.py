"""Tests of file opening"""

import io
import os

import pytest

import fiona
from fiona._crs import crs_to_wkt
from fiona.errors import DriverError


def test_open_shp(path_coutwildrnp_shp):
    """Open a shapefile"""
    assert fiona.open(path_coutwildrnp_shp)


def test_open_filename_with_exclamation(data_dir):
    path = os.path.relpath(os.path.join(data_dir, "!test.geojson"))
    assert os.path.exists(path), "Missing test data"
    assert fiona.open(path), "Failed to open !test.geojson"


@pytest.mark.xfail(raises=DriverError)
def test_write_memfile_crs_wkt():
    example_schema = {
        "geometry": "Point",
        "properties": [("title", "str")],
    }

    example_features = [
        {
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"title": "One"},
        },
        {
            "geometry": {"type": "Point", "coordinates": [1.0, 2.0]},
            "properties": {"title": "Two"},
        },
        {
            "geometry": {"type": "Point", "coordinates": [3.0, 4.0]},
            "properties": {"title": "Three"},
        },
    ]

    with io.BytesIO() as fd:
        with fiona.open(
            fd,
            "w",
            driver="GPKG",
            schema=example_schema,
            crs_wkt=crs_to_wkt("EPSG:32611"),
        ) as dst:
            dst.writerecords(example_features)

        fd.seek(0)
        with fiona.open(fd) as src:
            assert src.crs == {"init": "epsg:32611"}
