# coding: utf-8

import logging
import os
import shutil
import sys
import tempfile
import unittest

import six

import fiona

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class UnicodePathTest(unittest.TestCase):

    def setUp(self):
        tempdir = tempfile.mkdtemp()
        self.dir = os.path.join(tempdir, 'français')
        shutil.copytree('docs/data/', self.dir)

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.dir))

    def test_unicode_path(self):
        path = self.dir + '/test_uk.shp'
        if sys.version_info < (3,):
            path = path.decode('utf-8')
        with fiona.open(path) as c:
            assert len(c) == 48

    def test_unicode_path_layer(self):
        path = self.dir
        layer = 'test_uk'
        if sys.version_info < (3,):
            path = path.decode('utf-8')
            layer = layer.decode('utf-8')
        with fiona.open(path, layer=layer) as c:
            assert len(c) == 48

    def test_utf8_path(self):
        path = self.dir + '/test_uk.shp'
        if sys.version_info < (3,):
            with fiona.open(path) as c:
                assert len(c) == 48

