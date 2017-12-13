"""Test listing a datasource's layers."""

import logging
import sys
import unittest

import pytest

import fiona
import fiona.ogrext

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def test_single_file_private(path_coutwildrnp_shp):
    with fiona.drivers():
        assert fiona.ogrext._listlayers(
            path_coutwildrnp_shp) == ['coutwildrnp']


def test_single_file(path_coutwildrnp_shp):
    assert fiona.listlayers(path_coutwildrnp_shp) == ['coutwildrnp']


def test_directory(data_dir):
    assert fiona.listlayers(data_dir) == ['coutwildrnp', 'gre']


def test_directory_trailing_slash(data_dir):
    assert fiona.listlayers(data_dir) == ['coutwildrnp', 'gre']


def test_zip_path(path_coutwildrnp_zip):
    assert fiona.listlayers(
        'zip://{}'.format(path_coutwildrnp_zip)) == ['coutwildrnp']


def test_zip_path_arch(path_coutwildrnp_zip):
    vfs = 'zip://{}'.format(path_coutwildrnp_zip)
    assert fiona.listlayers('/coutwildrnp.shp', vfs=vfs) == ['coutwildrnp']


class ListLayersArgsTest(unittest.TestCase):

    def test_path(self):
        self.assertRaises(TypeError, fiona.listlayers, (1))

    def test_vfs(self):
        self.assertRaises(TypeError, fiona.listlayers, ("/"), vfs=1)

    def test_path_ioerror(self):
        self.assertRaises(IOError, fiona.listlayers, ("foobar"))
