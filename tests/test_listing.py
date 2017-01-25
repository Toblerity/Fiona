import logging
import os
import shutil
import sys
import unittest

import fiona
import fiona.ogrext

FIXME_WINDOWS = sys.platform.startswith("win")

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

def test_single_file_private():
    with fiona.drivers():
        assert fiona.ogrext._listlayers('tests/data/coutwildrnp.shp') == ['coutwildrnp']

def test_single_file():
    assert fiona.listlayers('tests/data/coutwildrnp.shp') == ['coutwildrnp']

def test_directory():
    assert fiona.listlayers('tests/data') == ['coutwildrnp']

@unittest.skipIf(FIXME_WINDOWS,
                 reason="FIXME on Windows. ValueError raised. Please look into why this test isn't working.")
def test_directory_trailing_slash():
    assert fiona.listlayers('tests/data/') == ['coutwildrnp']

def test_zip_path():
    assert fiona.listlayers('zip://tests/data/coutwildrnp.zip') == ['coutwildrnp']

def test_zip_path_arch():
    assert fiona.listlayers('/coutwildrnp.shp', vfs='zip://tests/data/coutwildrnp.zip') == ['coutwildrnp']

class ListLayersArgsTest(unittest.TestCase):
    def test_path(self):
        self.assertRaises(TypeError, fiona.listlayers, (1))
    def test_vfs(self):
        self.assertRaises(TypeError, fiona.listlayers, ("/"), vfs=1)
    def test_path_ioerror(self):
        self.assertRaises(IOError, fiona.listlayers, ("foobar"))

def test_parse_path():
    assert fiona.parse_paths("zip://foo.zip") == ("foo.zip", "zip", None)

def test_parse_path2():
    assert fiona.parse_paths("foo") == ("foo", None, None)

def test_parse_vfs():
    assert fiona.parse_paths("/", "zip://foo.zip") == ("/", "zip", "foo.zip")

