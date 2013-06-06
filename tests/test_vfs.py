import logging
import os
import shutil
import sys
import unittest

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

from .test_collection import ReadingTest

class ZipReadingTest(ReadingTest):
    
    def setUp(self):
        self.c = fiona.open("zip://docs/data/test_uk.zip", "r")
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.failUnlessEqual(
            repr(self.c),
            ("<open Collection '/vsizip/docs/data/test_uk.zip:0', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.failUnlessEqual(
            repr(self.c),
            ("<closed Collection '/vsizip/docs/data/test_uk.zip:0', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_path(self):
        self.failUnlessEqual(self.c.path, '/vsizip/docs/data/test_uk.zip')

class ZipArchiveReadingTest(ReadingTest):
    
    def setUp(self):
        self.c = fiona.open("/test_uk.shp", "r", vfs="zip://docs/data/test_uk.zip")
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.failUnlessEqual(
            repr(self.c),
            ("<open Collection '/vsizip/docs/data/test_uk.zip/test_uk.shp:0', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.failUnlessEqual(
            repr(self.c),
            ("<closed Collection '/vsizip/docs/data/test_uk.zip/test_uk.shp:0', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_path(self):
        self.failUnlessEqual(self.c.path, '/vsizip/docs/data/test_uk.zip/test_uk.shp')

class TarArchiveReadingTest(ReadingTest):
    
    def setUp(self):
        self.c = fiona.open("/testing/test_uk.shp", "r", vfs="tar://docs/data/test_uk.tar")
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.failUnlessEqual(
            repr(self.c),
            ("<open Collection '/vsitar/docs/data/test_uk.tar/testing/test_uk.shp:0', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.failUnlessEqual(
            repr(self.c),
            ("<closed Collection '/vsitar/docs/data/test_uk.tar/testing/test_uk.shp:0', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_path(self):
        self.failUnlessEqual(self.c.path, '/vsitar/docs/data/test_uk.tar/testing/test_uk.shp')

