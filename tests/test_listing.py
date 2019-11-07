"""Test listing a datasource's layers."""

import logging
import sys
import os

import pytest

import fiona
import fiona.ogrext
from fiona.errors import DriverError, FionaDeprecationWarning


def test_single_file_private(path_coutwildrnp_shp):
    with fiona.Env():
        assert fiona.ogrext._listlayers(
            path_coutwildrnp_shp) == ['coutwildrnp']


def test_single_file(path_coutwildrnp_shp):
    assert fiona.listlayers(path_coutwildrnp_shp) == ['coutwildrnp']


def test_directory(data_dir):
    assert sorted(fiona.listlayers(data_dir)) == ['coutwildrnp', 'gre', 'test_tin']


def test_directory_trailing_slash(data_dir):
    assert sorted(fiona.listlayers(data_dir)) == ['coutwildrnp', 'gre', 'test_tin']


def test_zip_path(path_coutwildrnp_zip):
    assert fiona.listlayers(
        'zip://{}'.format(path_coutwildrnp_zip)) == ['coutwildrnp']


def test_zip_path_arch(path_coutwildrnp_zip):
    vfs = 'zip://{}'.format(path_coutwildrnp_zip)
    with pytest.warns(FionaDeprecationWarning):
        assert fiona.listlayers('/coutwildrnp.shp', vfs=vfs) == ['coutwildrnp']


def test_list_not_existing(data_dir):
    """Test underlying Cython function correctly raises"""
    path = os.path.join(data_dir, "does_not_exist.geojson")
    with pytest.raises(DriverError):
        fiona.ogrext._listlayers(path)


def test_invalid_path():
    with pytest.raises(TypeError):
        fiona.listlayers(1)


def test_invalid_vfs():
    with pytest.raises(TypeError):
        fiona.listlayers("/", vfs=1)


def test_invalid_path_ioerror():
    with pytest.raises(DriverError):
        fiona.listlayers("foobar")


def test_listing_file(path_coutwildrnp_json):
    """list layers from an open file object"""
    with open(path_coutwildrnp_json, "rb") as f:
        assert len(fiona.listlayers(f)) == 1


def test_listing_pathobj(path_coutwildrnp_json):
    """list layers from a Path object"""
    pathlib = pytest.importorskip("pathlib")
    assert len(fiona.listlayers(pathlib.Path(path_coutwildrnp_json))) == 1
