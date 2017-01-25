import logging
import os
import shutil
import sys
import tempfile
import unittest

import fiona
from fiona.compat import OrderedDict

logging.basicConfig(stream=sys.stderr, level=logging.INFO)

FIXME_WINDOWS = sys.platform.startswith("win")

class ReadAccess(unittest.TestCase):
    # To check that we'll be able to get multiple 'r' connections to layers
    # in a single file.
    
    def setUp(self):
        self.c = fiona.open("tests/data/coutwildrnp.shp", "r", layer="coutwildrnp")
    
    def tearDown(self):
        self.c.close()

    def test_meta(self):
        with fiona.open("tests/data/coutwildrnp.shp", "r", layer="coutwildrnp") as c2:
            self.assertEqual(len(self.c), len(c2))
            self.assertEqual(sorted(self.c.schema.items()), sorted(c2.schema.items()))

    def test_meta(self):
        f1 = next(iter(self.c))
        with fiona.open("tests/data/coutwildrnp.shp", "r", layer="coutwildrnp") as c2:
            f2 = next(iter(c2))
            self.assertEqual(f1, f2)

@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. These tests raise PermissionErrors on Windows in Python 3.x (which doesn't exist in Python 2.7).  Please look into why this test isn't working.")
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
                'properties': [('title', 'str:80'), ('date', 'date')]},
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
        f2 = next(iter(c2))
        del f2['id']
        self.assertEqual(self.f, f2)

    def test_read_after_close(self):
        c2 = fiona.open(os.path.join(self.tempdir, "multi_write_test.shp"), "r")
        self.c.close()
        f2 = next(iter(c2))
        del f2['id']
        self.assertEqual(self.f, f2)

@unittest.skipIf(FIXME_WINDOWS, 
                    reason="FIXME on Windows. These tests raise PermissionErrors on Windows in Python 3.x (which doesn't exist in Python 2.7).  Please look into why this test isn't working.")
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
                'properties': [('title', 'str:80'), ('date', 'date')]},
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
        f2 = next(iter(c2))
        del f2['id']
        self.assertEqual(self.f, f2)

    def test_read_after_close(self):
        c2 = fiona.open(os.path.join(self.dir, "write_test.shp"), "r")
        self.c.close()
        f2 = next(iter(c2))
        del f2['id']
        self.assertEqual(self.f, f2)
