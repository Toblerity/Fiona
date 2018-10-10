import logging
import os
import shutil
import sys
import tempfile
import unittest

import pytest

import fiona
from .test_collection import ReadingTest


def test_index_selection(path_coutwildrnp_shp):
    with fiona.open(path_coutwildrnp_shp, 'r', layer=0) as c:
        assert len(c) == 67


@pytest.mark.usefixtures("unittest_path_coutwildrnp_shp")
class FileReadingTest(ReadingTest):

    def setUp(self):
        self.c = fiona.open(self.path_coutwildrnp_shp, 'r', layer='coutwildrnp')

    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '{path}:coutwildrnp', mode 'r' "
            "at {id}>".format(path=self.path_coutwildrnp_shp, id=hex(id(self.c)))))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '{path}:coutwildrnp', mode 'r' "
            "at {id}>".format(path=self.path_coutwildrnp_shp, id=hex(id(self.c)))))

    def test_name(self):
        self.assertEqual(self.c.name, 'coutwildrnp')


@pytest.mark.usefixtures("unittest_data_dir")
class DirReadingTest(ReadingTest):

    def setUp(self):
        self.c = fiona.open(self.data_dir, "r", layer="coutwildrnp")

    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '{path}:coutwildrnp', mode 'r' "
            "at {id}>".format(path=self.data_dir, id=hex(id(self.c)))))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '{path}:coutwildrnp', mode 'r' "
            "at {id}>".format(path=self.data_dir, id=hex(id(self.c)))))

    def test_name(self):
        self.assertEqual(self.c.name, 'coutwildrnp')

    def test_path(self):
        self.assertEqual(self.c.path, self.data_dir)


@pytest.mark.usefixtures("unittest_path_coutwildrnp_shp")
class InvalidLayerTest(unittest.TestCase):

    def test_invalid(self):
        self.assertRaises(ValueError, fiona.open, (self.path_coutwildrnp_shp), layer="foo")

    def test_write_numeric_layer(self):
        self.assertRaises(ValueError, fiona.open,
                          (os.path.join(tempfile.gettempdir(), "test-no-iter.shp")),
                          mode='w', layer=0)
