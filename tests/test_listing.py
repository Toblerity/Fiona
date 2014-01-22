import logging
import os
import shutil
import sys
import unittest

import fiona
import fiona.ogrext

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

def test_single_file_private():
    with fiona.drivers():
        assert fiona.ogrext._listlayers('docs/data/test_uk.shp') == ['test_uk']

def test_single_file():
    assert fiona.listlayers('docs/data/test_uk.shp') == ['test_uk']

def test_directory():
    assert fiona.listlayers('docs/data') == ['test_uk']

def test_directory_trailing_slash():
    assert fiona.listlayers('docs/data/') == ['test_uk']

def test_zip_path():
    assert fiona.listlayers('zip://docs/data/test_uk.zip') == ['test_uk']

def test_zip_path_arch():
    assert fiona.listlayers('/test_uk.shp', vfs='zip://docs/data/test_uk.zip') == ['test_uk']

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

