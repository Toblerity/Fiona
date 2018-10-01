"""Tests of file opening"""

import fiona


def test_open_shp(path_coutwildrnp_shp):
    """Open a shapefile"""
    assert fiona.open(path_coutwildrnp_shp)
