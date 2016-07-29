import logging
import sys
import os

import pytest

import fiona


logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


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


def test_remove(tmpdir):
    outdir = str(tmpdir.mkdir('test_remove'))
    filename_shp = os.path.join(outdir, 'test.shp')
    
    create_sample_data(filename_shp, driver='ESRI Shapefile')
    fiona.remove(filename_shp, driver='ESRI Shapefile')
    assert(not os.path.exists(filename_shp))
    
    with pytest.raises(RuntimeError):
        fiona.remove(filename_shp, driver='ESRI Shapefile')


def test_remove_driver(tmpdir):
    outdir = str(tmpdir.mkdir('test_remove_driver'))
    filename_shp = os.path.join(outdir, 'test.shp')
    filename_json = os.path.join(outdir, 'test.json')
        
    create_sample_data(filename_shp, driver='ESRI Shapefile')
    create_sample_data(filename_json, driver='GeoJSON')
    fiona.remove(filename_json, driver='GeoJSON')
    assert(not os.path.exists(filename_json))
    assert(os.path.exists(filename_shp))


def test_remove_collection(tmpdir):
    outdir = str(tmpdir.mkdir('test_remove_collection'))
    filename_shp = os.path.join(outdir, 'test.shp')
    
    create_sample_data(filename_shp, driver='ESRI Shapefile')
    collection = fiona.open(filename_shp, 'r')
    fiona.remove(collection)
    assert(not os.path.exists(filename_shp))


def test_remove_path_without_driver(tmpdir):
    outdir = str(tmpdir.mkdir('test_remove_path_without_driver'))
    filename_shp = os.path.join(outdir, 'test.shp')

    create_sample_data(filename_shp, driver='ESRI Shapefile')

    with pytest.raises(Exception):
        fiona.remove(filename_shp)

    assert(os.path.exists(filename_shp))
