"""Tests of file opening"""

import fiona


def test_open_shp():
    """Open a shapefile"""
    assert fiona.open("tests/data/coutwildrnp.shp")
