"""Tests of MemoryFile and ZippedMemoryFile"""

import os
from io import BytesIO
import pytest
import uuid

import fiona
from fiona.io import MemoryFile, ZipMemoryFile

from .conftest import requires_gpkg


@pytest.fixture(scope='session')
def profile_first_coutwildrnp_shp(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp) as col:
        return col.profile, next(iter(col))


def test_memoryfile(path_coutwildrnp_json):
    """In-memory GeoJSON file can be read"""
    with open(path_coutwildrnp_json, 'rb') as f:
        data = f.read()
    with MemoryFile(data) as memfile:
        with memfile.open() as collection:
            assert len(collection) == 67


def test_zip_memoryfile(bytes_coutwildrnp_zip):
    """In-memory zipped Shapefile can be read"""
    with ZipMemoryFile(bytes_coutwildrnp_zip) as memfile:
        with memfile.open('coutwildrnp.shp') as collection:
            assert len(collection) == 67


def test_zip_memoryfile_infer_layer_name(bytes_coutwildrnp_zip):
    """In-memory zipped Shapefile can be read with the default layer"""
    with ZipMemoryFile(bytes_coutwildrnp_zip) as memfile:
        with memfile.open() as collection:
            assert len(collection) == 67


def test_write_memoryfile(profile_first_coutwildrnp_shp):
    """In-memory Shapefile can be written"""
    profile, first = profile_first_coutwildrnp_shp
    profile['driver'] = 'GeoJSON'
    with MemoryFile() as memfile:
        with memfile.open(**profile) as col:
            col.write(first)
        memfile.seek(0)
        data = memfile.read()

    with MemoryFile(data) as memfile:
        with memfile.open() as col:
            assert len(col) == 1


def test_memoryfile_bytesio(path_coutwildrnp_json):
    """In-memory GeoJSON file can be read"""
    with open(path_coutwildrnp_json, 'rb') as f:
        data = f.read()

    with fiona.open(BytesIO(data)) as collection:
        assert len(collection) == 67


def test_memoryfile_fileobj(path_coutwildrnp_json):
    """In-memory GeoJSON file can be read"""
    with open(path_coutwildrnp_json, 'rb') as f:

        with fiona.open(f) as collection:
            assert len(collection) == 67


def test_write_memoryfile_(profile_first_coutwildrnp_shp):
    """In-memory Shapefile can be written"""
    profile, first = profile_first_coutwildrnp_shp
    profile['driver'] = 'GeoJSON'
    with BytesIO() as fout:
        with fiona.open(fout, 'w', **profile) as col:
            col.write(first)
        fout.seek(0)
        data = fout.read()

    with MemoryFile(data) as memfile:
        with memfile.open() as col:
            assert len(col) == 1


@requires_gpkg
def test_read_multilayer_memoryfile(path_coutwildrnp_json, tmpdir):
    """Test read access to multilayer dataset in from file-like object"""
    with fiona.open(path_coutwildrnp_json, "r") as src:
        schema = src.schema
        features = list(src)

    path = os.path.join(tmpdir, "test.gpkg")
    with fiona.open(path, "w", driver="GPKG", schema=schema, layer="layer1") as dst:
        dst.writerecords(features[0:5])
    with fiona.open(path, "w", driver="GPKG", schema=schema, layer="layer2") as dst:
        dst.writerecords(features[5:])

    with open(path, "rb") as f:
        with fiona.open(f, layer="layer1") as src:
            assert src.name == "layer1"
            assert len(src) == 5
    # Bug reported in #781 where this next section would fail
    with open(path, "rb") as f:
        with fiona.open(f, layer="layer2") as src:
            assert src.name == "layer2"
            assert len(src) == 62
