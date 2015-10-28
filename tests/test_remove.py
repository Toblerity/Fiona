import logging
import sys
import os

import pytest

import fiona


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


def create_test_data(filename, driver):
    meta = {
        'driver': driver,
        'schema': {
            'geometry': 'Point',
            'properties': {}
        }
    }
    with fiona.open(filename, 'w', **meta) as dst:
        dst.write({
            'geometry': {
                'type': 'Point',
                'coordinates': (0, 0),
            },
            'properties': {},
        })
    assert(os.path.exists(filename))


def test_remove(tmpdir):
    filename_shp = str(tmpdir.join('test.shp'))
    
    create_test_data(filename_shp, driver='ESRI Shapefile')
    fiona.remove(filename_shp, driver='ESRI Shapefile')
    assert(not os.path.exists(filename_shp))
    
    with pytest.raises(RuntimeError):
        fiona.remove(filename_shp, driver='ESRI Shapefile')

def test_remove_driver(tmpdir):
    filename_shp = str(tmpdir.join('test.shp'))
    filename_json = str(tmpdir.join('test.json'))
    
    create_test_data(filename_shp, driver='ESRI Shapefile')
    create_test_data(filename_json, driver='GeoJSON')
    fiona.remove(filename_json, driver='GeoJSON')
    assert(not os.path.exists(filename_json))
    assert(os.path.exists(filename_shp))

def test_remove_collection(tmpdir):
    filename_shp = str(tmpdir.join('test.shp'))
    create_test_data(filename_shp, driver='ESRI Shapefile')
    collection = fiona.open(filename_shp, 'r')
    fiona.remove(collection)
    assert(not os.path.exists(filename_shp))
