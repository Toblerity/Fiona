import logging
import sys
import os

import tempfile
import pytest

import fiona


logging.basicConfig(stream=sys.stderr, level=logging.INFO)


def create_sample_data(filename, driver):
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


def test_remove(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
    filename_shp = os.path.join(tmpdir, 'test.shp')
    
    create_sample_data(filename_shp, driver='ESRI Shapefile')
    fiona.remove(filename_shp, driver='ESRI Shapefile')
    assert(not os.path.exists(filename_shp))
    
    with pytest.raises(RuntimeError):
        fiona.remove(filename_shp, driver='ESRI Shapefile')

def test_remove_driver(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
    filename_shp = os.path.join(tmpdir, 'test.shp')
    filename_json = os.path.join(tmpdir, 'test.json')
        
    create_sample_data(filename_shp, driver='ESRI Shapefile')
    create_sample_data(filename_json, driver='GeoJSON')
    fiona.remove(filename_json, driver='GeoJSON')
    assert(not os.path.exists(filename_json))
    assert(os.path.exists(filename_shp))

def test_remove_collection(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
    filename_shp = os.path.join(tmpdir, 'test.shp')
    
    create_sample_data(filename_shp, driver='ESRI Shapefile')
    collection = fiona.open(filename_shp, 'r')
    fiona.remove(collection)
    assert(not os.path.exists(filename_shp))

def test_remove_path_without_driver(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
    filename_shp = os.path.join(tmpdir, 'test.shp')

    create_sample_data(filename_shp, driver='ESRI Shapefile')

    with pytest.raises(Exception):
        fiona.remove(filename_shp)

    assert(os.path.exists(filename_shp))
