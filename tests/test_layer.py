import logging
import os
import shutil
import sys
import tempfile
import unittest

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

from .test_collection import ReadingTest

def test_index_selection():
    with fiona.open('tests/data/coutwildrnp.shp', 'r', layer=0) as c:
        assert len(c) == 67

class FileReadingTest(ReadingTest):
    
    def setUp(self):
        self.c = fiona.open('tests/data/coutwildrnp.shp', 'r', layer='coutwildrnp')
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection 'tests/data/coutwildrnp.shp:coutwildrnp', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection 'tests/data/coutwildrnp.shp:coutwildrnp', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_name(self):
        self.assertEqual(self.c.name, 'coutwildrnp')

class DirReadingTest(ReadingTest):
    
    def setUp(self):
        self.c = fiona.open("tests/data", "r", layer="coutwildrnp")
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection 'tests/data:coutwildrnp', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection 'tests/data:coutwildrnp', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_name(self):
        self.assertEqual(self.c.name, 'coutwildrnp')

    def test_path(self):
        self.assertEqual(self.c.path, "tests/data")

class InvalidLayerTest(unittest.TestCase):

    def test_invalid(self):
        self.assertRaises(ValueError, fiona.open, ("tests/data/coutwildrnp.shp"), layer="foo")

    def test_write_numeric_layer(self):
        self.assertRaises(ValueError, fiona.open,
                          (os.path.join(tempfile.gettempdir(), "test-no-iter.shp")),
                          mode='w', layer=0)
