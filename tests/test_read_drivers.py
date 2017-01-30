import logging
import sys

import pytest

import fiona
from fiona.errors import FionaValueError


logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def test_read_fail():
    with pytest.raises(FionaValueError):
        fiona.open('tests/data/coutwildrnp.shp', driver='GeoJSON')
    with pytest.raises(FionaValueError):
        fiona.open('tests/data/coutwildrnp.shp', enabled_drivers=['GeoJSON'])


def test_read():
    with fiona.open(
            'tests/data/coutwildrnp.shp', driver='ESRI Shapefile') as src:
        assert src.driver == 'ESRI Shapefile'
    with fiona.open(
            'tests/data/coutwildrnp.shp',
            enabled_drivers=['GeoJSON', 'ESRI Shapefile']) as src:
        assert src.driver == 'ESRI Shapefile'
