"""Tests of MemoryFile and ZippedMemoryFile"""

from io import BytesIO
import pytest
import uuid

import fiona
from fiona.io import MemoryFile, ZipMemoryFile


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
