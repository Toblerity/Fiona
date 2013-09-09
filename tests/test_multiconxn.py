import logging
import os
import shutil
import sys
import tempfile
import unittest

import fiona
from fiona.odict import OrderedDict

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class ReadAccess(unittest.TestCase):
    # To check that we'll be able to get multiple 'r' connections to layers
    # in a single file.
    
    def setUp(self):
        self.c = fiona.open("docs/data/test_uk.shp", "r", layer="test_uk")
    
    def tearDown(self):
        self.c.close()

    def test_meta(self):
        with fiona.open("docs/data/test_uk.shp", "r", layer="test_uk") as c2:
            self.assertEqual(len(self.c), len(c2))
            self.assertEqual(sorted(self.c.schema.items()), sorted(c2.schema.items()))

    def test_meta(self):
        f1 = next(self.c)
        with fiona.open("docs/data/test_uk.shp", "r", layer="test_uk") as c2:
            f2 = next(c2)
            self.assertEqual(f1, f2)

class ReadWriteAccess(unittest.TestCase):
    # To check that we'll be able to read from a file that we're
    # writing to.
    
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.c = fiona.open(
            os.path.join(self.tempdir, "multi_write_test.shp"),
            "w",
            driver="ESRI Shapefile",
            schema={
                'geometry': 'Point', 
                'properties': [('title', 'str'), ('date', 'date')]},
            crs={'init': "epsg:4326", 'no_defs': True},
            encoding='utf-8')
        self.f = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': OrderedDict([('title', 'point one'), ('date', '2012-01-29')])}
        self.c.writerecords([self.f])
        self.c.flush()

    def tearDown(self):
        self.c.close()
        shutil.rmtree(self.tempdir)

    def test_meta(self):
        c2 = fiona.open(os.path.join(self.tempdir, "multi_write_test.shp"), "r")
        self.assertEqual(len(self.c), len(c2))
        self.assertEqual(sorted(self.c.schema.items()), sorted(c2.schema.items()))

    def test_read(self):
        c2 = fiona.open(os.path.join(self.tempdir, "multi_write_test.shp"), "r")
        f2 = next(c2)
        del f2['id']
        self.assertEqual(self.f, f2)

    def test_read_after_close(self):
        c2 = fiona.open(os.path.join(self.tempdir, "multi_write_test.shp"), "r")
        self.c.close()
        f2 = next(c2)
        del f2['id']
        self.assertEqual(self.f, f2)

class LayerCreation(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.dir = os.path.join(self.tempdir, 'layer_creation')
        if os.path.exists(self.dir):
            shutil.rmtree(self.dir)
        os.mkdir(self.dir)
        self.c = fiona.open(
            self.dir,
            'w',
            layer='write_test',
            driver='ESRI Shapefile',
            schema={
                'geometry': 'Point', 
                'properties': [('title', 'str'), ('date', 'date')]},
            crs={'init': "epsg:4326", 'no_defs': True},
            encoding='utf-8')
        self.f = {
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': OrderedDict([('title', 'point one'), ('date', '2012-01-29')])}
        self.c.writerecords([self.f])
        self.c.flush()

    def tearDown(self):
        self.c.close()
        shutil.rmtree(self.tempdir)

    def test_meta(self):
        c2 = fiona.open(os.path.join(self.dir, "write_test.shp"), "r")
        self.assertEqual(len(self.c), len(c2))
        self.assertEqual(sorted(self.c.schema.items()), sorted(c2.schema.items()))

    def test_read(self):
        c2 = fiona.open(os.path.join(self.dir, "write_test.shp"), "r")
        f2 = next(c2)
        del f2['id']
        self.assertEqual(self.f, f2)

    def test_read_after_close(self):
        c2 = fiona.open(os.path.join(self.dir, "write_test.shp"), "r")
        self.c.close()
        f2 = next(c2)
        del f2['id']
        self.assertEqual(self.f, f2)

