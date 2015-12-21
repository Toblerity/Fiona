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
        shutil.copytree('tests/data/', self.dir)

    def tearDown(self):
        shutil.rmtree(os.path.dirname(self.dir))

    def test_unicode_path(self):
        path = self.dir + '/coutwildrnp.shp'
        if sys.version_info < (3,):
            path = path.decode('utf-8')
        with fiona.open(path) as c:
            assert len(c) == 67

    def test_unicode_path_layer(self):
        path = self.dir
        layer = 'coutwildrnp'
        if sys.version_info < (3,):
            path = path.decode('utf-8')
            layer = layer.decode('utf-8')
        with fiona.open(path, layer=layer) as c:
            assert len(c) == 67

    def test_utf8_path(self):
        path = self.dir + '/coutwildrnp.shp'
        if sys.version_info < (3,):
            with fiona.open(path) as c:
                assert len(c) == 67


class UnicodeStringFieldTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_write(self):
        schema = {
            'geometry': 'Point',
            'properties': {'label': 'str', u'verit\xe9': 'int'}}
        with fiona.open(os.path.join(self.tempdir, "test-write.shp"),
                        "w", "ESRI Shapefile", schema=schema,
                        encoding='utf-8') as c:
            c.writerecords([
                {'type': 'Feature', 'geometry': {'type': 'Point',
                                                 'coordinates': [0, 0]},
                                    'properties': {'label': u'Ba\u2019kelalan',
                                                   u'verit\xe9': 0}}])

        with fiona.open(os.path.join(self.tempdir)) as c:
            f = next(c)
            self.assertEquals(f['properties']['label'], u'Ba\u2019kelalan')
            self.assertEquals(f['properties'][u'verit\xe9'], 0)
