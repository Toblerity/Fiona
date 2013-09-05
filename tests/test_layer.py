import logging
import os
import shutil
import sys
import tempfile
import unittest

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

from .test_collection import ReadingTest

def test_index_selection():
    with fiona.open('docs/data/test_uk.shp', 'r', layer=0) as c:
        assert len(c) == 48

class FileReadingTest(ReadingTest):
    
    def setUp(self):
        self.c = fiona.open('docs/data/test_uk.shp', 'r', layer='test_uk')
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.failUnlessEqual(
            repr(self.c),
            ("<open Collection 'docs/data/test_uk.shp:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.failUnlessEqual(
            repr(self.c),
            ("<closed Collection 'docs/data/test_uk.shp:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_name(self):
        self.failUnlessEqual(self.c.name, 'test_uk')

class DirReadingTest(ReadingTest):
    
    def setUp(self):
        self.c = fiona.open("docs/data", "r", layer="test_uk")
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.failUnlessEqual(
            repr(self.c),
            ("<open Collection 'docs/data:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.failUnlessEqual(
            repr(self.c),
            ("<closed Collection 'docs/data:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_name(self):
        self.failUnlessEqual(self.c.name, 'test_uk')

    def test_path(self):
        self.failUnlessEqual(self.c.path, "docs/data")

class InvalidLayerTest(unittest.TestCase):

    def test_invalid(self):
        self.assertRaises(ValueError, fiona.open, ("docs/data/test_uk.shp"), layer="foo")

    def test_write_numeric_layer(self):
        self.assertRaises(ValueError, fiona.open,
                          (os.path.join(tempfile.gettempdir(), "test-no-iter.shp")),
                          mode='w', layer=0)
