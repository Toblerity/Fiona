import logging
import os
import shutil
import sys
import unittest

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

from .test_collection import ReadingTest


class VsiReadingTest(ReadingTest):
    
    # There's a bug in GDAL 1.9.2 http://trac.osgeo.org/gdal/ticket/5093
    # in which the VSI driver reports the wrong number of features.
    # I'm overriding ReadingTest's test_filter_1 with a function that
    # passes and creating a new method in this class that we can exclude
    # from the test runner at run time.

    def test_filter_vsi(self):
        results = list(self.c.filter(bbox=(-114.0, 35.0, -104, 45.0)))
        self.assertEqual(len(results), 67)
        f = results[0]
        self.assertEqual(f['id'], "0")
        self.assertEqual(f['properties']['STATE'], 'UT')


class ZipReadingTest(VsiReadingTest):
    
    def setUp(self):
        self.c = fiona.open("zip://tests/data/coutwildrnp.zip", "r")

    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '/vsizip/tests/data/coutwildrnp.zip:coutwildrnp', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '/vsizip/tests/data/coutwildrnp.zip:coutwildrnp', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_path(self):
        self.assertEqual(self.c.path, '/vsizip/tests/data/coutwildrnp.zip')


class ZipArchiveReadingTest(VsiReadingTest):
    
    def setUp(self):
        self.c = fiona.open("/coutwildrnp.shp", "r", vfs="zip://tests/data/coutwildrnp.zip")
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '/vsizip/tests/data/coutwildrnp.zip/coutwildrnp.shp:coutwildrnp', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '/vsizip/tests/data/coutwildrnp.zip/coutwildrnp.shp:coutwildrnp', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_path(self):
        self.assertEqual(self.c.path, '/vsizip/tests/data/coutwildrnp.zip/coutwildrnp.shp')


class ZipArchiveReadingTestAbsPath(ZipArchiveReadingTest):

    def setUp(self):
        self.c = fiona.open(
                "/coutwildrnp.shp", "r",
                vfs="zip://" + os.path.abspath("tests/data/coutwildrnp.zip"))

    def test_open_repr(self):
        self.assert_(repr(self.c).startswith("<open Collection '/vsizip/"))

    def test_closed_repr(self):
        self.c.close()
        self.assert_(repr(self.c).startswith("<closed Collection '/vsizip/"))

    def test_path(self):
        self.assert_(self.c.path.startswith('/vsizip/'))


class TarArchiveReadingTest(VsiReadingTest):
    
    def setUp(self):
        self.c = fiona.open("/testing/coutwildrnp.shp", "r", vfs="tar://tests/data/coutwildrnp.tar")
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '/vsitar/tests/data/coutwildrnp.tar/testing/coutwildrnp.shp:coutwildrnp', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '/vsitar/tests/data/coutwildrnp.tar/testing/coutwildrnp.shp:coutwildrnp', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_path(self):
        self.assertEqual(self.c.path, '/vsitar/tests/data/coutwildrnp.tar/testing/coutwildrnp.shp')

