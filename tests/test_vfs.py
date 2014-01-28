import logging
import os
import shutil
import sys
import unittest

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

from .test_collection import ReadingTest


class VsiReadingTest(ReadingTest):
    
    # There's a bug in GDAL 1.9.2 http://trac.osgeo.org/gdal/ticket/5093
    # in which the VSI driver reports the wrong number of features.
    # I'm overriding ReadingTest's test_filter_1 with a function that
    # passes and creating a new method in this class that we can exclude
    # from the test runner at run time.

    def test_filter_vsi(self):
        results = list(self.c.filter(bbox=(-15.0, 35.0, 15.0, 65.0)))
        self.failUnlessEqual(len(results), 48)
        f = results[0]
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')

class ZipReadingTest(VsiReadingTest):
    
    def setUp(self):
        self.c = fiona.open("zip://docs/data/test_uk.zip", "r")
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.failUnlessEqual(
            repr(self.c),
            ("<open Collection '/vsizip/docs/data/test_uk.zip:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.failUnlessEqual(
            repr(self.c),
            ("<closed Collection '/vsizip/docs/data/test_uk.zip:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_path(self):
        self.failUnlessEqual(self.c.path, '/vsizip/docs/data/test_uk.zip')

class ZipArchiveReadingTest(VsiReadingTest):
    
    def setUp(self):
        self.c = fiona.open("/test_uk.shp", "r", vfs="zip://docs/data/test_uk.zip")
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.failUnlessEqual(
            repr(self.c),
            ("<open Collection '/vsizip/docs/data/test_uk.zip/test_uk.shp:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.failUnlessEqual(
            repr(self.c),
            ("<closed Collection '/vsizip/docs/data/test_uk.zip/test_uk.shp:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_path(self):
        self.failUnlessEqual(self.c.path, '/vsizip/docs/data/test_uk.zip/test_uk.shp')

class TarArchiveReadingTest(VsiReadingTest):
    
    def setUp(self):
        self.c = fiona.open("/testing/test_uk.shp", "r", vfs="tar://docs/data/test_uk.tar")
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.failUnlessEqual(
            repr(self.c),
            ("<open Collection '/vsitar/docs/data/test_uk.tar/testing/test_uk.shp:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.failUnlessEqual(
            repr(self.c),
            ("<closed Collection '/vsitar/docs/data/test_uk.tar/testing/test_uk.shp:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_path(self):
        self.failUnlessEqual(self.c.path, '/vsitar/docs/data/test_uk.tar/testing/test_uk.shp')

