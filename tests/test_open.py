"""Tests of file opening"""

import os
import fiona


def test_open_shp(path_coutwildrnp_shp):
    """Open a shapefile"""
    assert fiona.open(path_coutwildrnp_shp)


def test_open_filename_with_exclamation(data_dir):
    path = os.path.relpath(os.path.join(data_dir, "!test.geojson"))
    assert os.path.exists(path), "Missing test data"
    assert fiona.open(path), "Failed to open !test.geojson"
