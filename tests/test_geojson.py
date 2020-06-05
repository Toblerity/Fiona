import os

import pytest

import fiona
from fiona.collection import supported_drivers
from fiona.crs import from_epsg
from fiona.errors import FionaValueError, DriverError, SchemaError, CRSError


def test_json_read(path_coutwildrnp_json):
    with fiona.open(path_coutwildrnp_json, 'r') as c:
        assert len(c) == 67


def test_json(tmpdir):
    """Write a simple GeoJSON file"""
    path = tmpdir.join('foo.json').strpath
    with fiona.open(path, 'w',
                    driver='GeoJSON',
                    schema={'geometry': 'Unknown',
                            'properties': [('title', 'str')]}) as c:
        c.writerecords([{
            'geometry': {'type': 'Point', 'coordinates': [0.0, 0.0]},
            'properties': {'title': 'One'}}])
        c.writerecords([{
            'geometry': {'type': 'MultiPoint', 'coordinates': [[0.0, 0.0]]},
            'properties': {'title': 'Two'}}])
    with fiona.open(path) as c:
        assert c.schema['geometry'] == 'Unknown'
        assert len(c) == 2


def test_json_overwrite(tmpdir):
    """Overwrite an existing GeoJSON file"""
    path = tmpdir.join('foo.json').strpath

    driver = "GeoJSON"
    schema1 = {"geometry": "Unknown", "properties": [("title", "str")]}
    schema2 = {"geometry": "Unknown", "properties": [("other", "str")]}

    features1 = [
        {
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"title": "One"},
        },
        {
            "geometry": {"type": "MultiPoint", "coordinates": [[0.0, 0.0]]},
            "properties": {"title": "Two"},
        }
    ]
    features2 = [
        {
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"other": "Three"},
        },
    ]

    # write some data to a file
    with fiona.open(path, "w", driver=driver, schema=schema1) as c:
        c.writerecords(features1)

    # test the data was written correctly
    with fiona.open(path, "r") as c:
        assert len(c) == 2
        feature = next(iter(c))
        assert feature["properties"]["title"] == "One"

    # attempt to overwrite the existing file with some new data
    with fiona.open(path, "w", driver=driver, schema=schema2) as c:
        c.writerecords(features2)

    # test the second file was written correctly
    with fiona.open(path, "r") as c:
        assert len(c) == 1
        feature = next(iter(c))
        assert feature["properties"]["other"] == "Three"


def test_json_overwrite_invalid(tmpdir):
    """Overwrite an existing file that isn't a valid GeoJSON"""

    # write some invalid data to a file
    path = tmpdir.join('foo.json').strpath
    with open(path, "w") as f:
        f.write("This isn't a valid GeoJSON file!!!")

    schema1 = {"geometry": "Unknown", "properties": [("title", "str")]}
    features1 = [
        {
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"title": "One"},
        },
        {
            "geometry": {"type": "MultiPoint", "coordinates": [[0.0, 0.0]]},
            "properties": {"title": "Two"},
        }
    ]

    # attempt to overwrite it with a valid file
    with fiona.open(path, "w", driver="GeoJSON", schema=schema1) as dst:
        dst.writerecords(features1)

    # test the data was written correctly
    with fiona.open(path, "r") as src:
        assert len(src) == 2


def test_write_json_invalid_directory(tmpdir):
    """Attempt to create a file in a directory that doesn't exist"""
    path = tmpdir.join('does-not-exist', 'foo.json').strpath
    schema = {"geometry": "Unknown", "properties": [("title", "str")]}
    with pytest.raises(DriverError):
        fiona.open(path, "w", driver="GeoJSON", schema=schema)


def test_overwrite_shp_with_json_clears_auxiliary_files(tmpdir):
    """ Test that auxiliary files are also removed if dataset is overwritten"""
    schema1 = {"geometry": "Point", "properties": [("title", "str")]}
    features1 = [
        {
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"title": "One"},
        },
        {
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"title": "Two"},
        }
    ]

    path = tmpdir.join('foo.shp').strpath
    # attempt to overwrite it with a valid file
    with fiona.open(path, "w", driver="ESRI Shapefile", schema=schema1) as dst:
        dst.writerecords(features1)

    assert set(os.listdir(tmpdir.strpath)) == {'foo.cpg', 'foo.dbf', 'foo.shx', 'foo.shp'}

    # attempt to overwrite it with a GeoJSON file
    with fiona.open(path, "w", driver="GeoJSON", schema=schema1) as dst:
        dst.writerecords(features1)

    assert os.listdir(tmpdir.strpath) == ['foo.shp']


def test_overwrite_shp_with_json_clears_auxiliary_files_different_extension(tmpdir):
    """ Test that auxiliary files are also removed if dataset is overwritten"""
    schema1 = {"geometry": "Point", "properties": [("title", "str")]}
    features1 = [
        {
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"title": "One"},
        },
        {
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"title": "Two"},
        }
    ]

    path = tmpdir.join('foo.shp').strpath
    # attempt to overwrite it with a valid file
    with fiona.open(path, "w", driver="ESRI Shapefile", schema=schema1) as dst:
        dst.writerecords(features1)

    assert set(os.listdir(tmpdir.strpath)) == {'foo.cpg', 'foo.dbf', 'foo.shx', 'foo.shp'}

    # attempt to overwrite it with a GeoJSON file
    path = tmpdir.join('foo.shx').strpath
    with fiona.open(path, "w", driver="GeoJSON", schema=schema1) as dst:
        dst.writerecords(features1)

    assert os.listdir(tmpdir.strpath) == ['foo.shx']


def test_overwrite_no(tmpdir, caplog):
    """ Test that no "ERROR:fiona._env:/tmp/test.geojson: No such file or directory" message
        is shown if geojson is overwritten"""

    schema = {"geometry": "Point", "properties": [("title", "str")]}
    features = [
        {
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"title": "One"},
        },
        {
            "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            "properties": {"title": "Two"},
        }
    ]

    path = tmpdir.join('foo.json').strpath

    for i in range(2):
        with fiona.open(path, "w",
                        driver="GeoJSON",
                        schema=schema,
                        crs=from_epsg(4326)) as sink:
            sink.writerecords(features)

    assert "No such file or directory" not in caplog.text
