import logging
import os
import shutil
import sys
import unittest

import fiona
import fiona.ogrext

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

def test_single_file_private():
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

