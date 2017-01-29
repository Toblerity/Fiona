import logging
import os
import shutil
import sys
import tempfile
import unittest

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

from .test_collection import ReadingTest

WILDSHP = os.path.join('tests', 'data','coutwildrnp.shp')
DATA_DIR = os.path.join('tests', 'data')

def test_index_selection():
    with fiona.open(WILDSHP, 'r', layer=0) as c:
        assert len(c) == 67

class FileReadingTest(ReadingTest):

    def setUp(self):
        self.c = fiona.open(WILDSHP, 'r', layer='coutwildrnp')

    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '{path}:coutwildrnp', mode 'r' "
            "at {id}>".format(path=WILDSHP, id=hex(id(self.c)))))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '{path}:coutwildrnp', mode 'r' "
            "at {id}>".format(path=WILDSHP, id=hex(id(self.c)))))

    def test_name(self):
        self.assertEqual(self.c.name, 'coutwildrnp')

class DirReadingTest(ReadingTest):

    def setUp(self):
        self.c = fiona.open(DATA_DIR, "r", layer="coutwildrnp")

    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '{path}:coutwildrnp', mode 'r' "
            "at {id}>".format(path=DATA_DIR, id=hex(id(self.c)))))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '{path}:coutwildrnp', mode 'r' "
            "at {id}>".format(path=DATA_DIR, id=hex(id(self.c)))))

    def test_name(self):
        self.assertEqual(self.c.name, 'coutwildrnp')

    def test_path(self):
        self.assertEqual(self.c.path, DATA_DIR)

class InvalidLayerTest(unittest.TestCase):

    def test_invalid(self):
        self.assertRaises(ValueError, fiona.open, (WILDSHP), layer="foo")

    def test_write_numeric_layer(self):
        self.assertRaises(ValueError, fiona.open,
                          (os.path.join(tempfile.gettempdir(), "test-no-iter.shp")),
                          mode='w', layer=0)
