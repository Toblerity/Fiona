# testing features, to be called by nosetests

import logging
import os
import shutil
import sys
import tempfile
import unittest

import fiona
from fiona import collection
from fiona.collection import Collection
from fiona.ogrext import featureRT

#logging.basicConfig(stream=sys.stderr, level=logging.INFO)

class PointRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        schema = {'geometry': 'Point', 'properties': {'title': 'str'}}
        self.c = Collection(os.path.join(self.tempdir, "foo.shp"),
                            "w", driver="ESRI Shapefile", schema=schema)
    def tearDown(self):
        self.c.close()
        shutil.rmtree(self.tempdir)
    def test_geometry(self):
        f = { 'id': '1', 
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        self.assertEqual(
            sorted(g['geometry'].items()),
            [('coordinates', (0.0, 0.0)), ('type', 'Point')])
    def test_properties(self):
        f = { 'id': '1', 
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        self.assertEqual(g['properties']['title'], 'foo')
    def test_none_property(self):
        f = { 'id': '1',
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': None} }
        g = featureRT(f, self.c)
        self.assertEqual(g['properties']['title'], None)

class LineStringRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        schema = {'geometry': 'LineString', 'properties': {'title': 'str'}}
        self.c = Collection(os.path.join(self.tempdir, "foo.shp"),
                            "w", "ESRI Shapefile", schema=schema)
    def tearDown(self):
        self.c.close()
        shutil.rmtree(self.tempdir)
    def test_geometry(self):
        f = { 'id': '1', 
              'geometry': { 'type': 'LineString', 
                            'coordinates': [(0.0, 0.0), (1.0, 1.0)] },
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        self.assertEqual(
            sorted(g['geometry'].items()),
            [('coordinates', [(0.0, 0.0), (1.0, 1.0)]), 
             ('type', 'LineString')])
    def test_properties(self):
        f = { 'id': '1',
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        self.assertEqual(g['properties']['title'], 'foo')

class PolygonRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        schema = {'geometry': 'Polygon', 'properties': {'title': 'str'}}
        self.c = Collection(os.path.join(self.tempdir, "foo.shp"),
                            "w", "ESRI Shapefile", schema=schema)
    def tearDown(self):
        self.c.close()
        shutil.rmtree(self.tempdir)
    def test_geometry(self):
        f = { 'id': '1', 
              'geometry': { 'type': 'Polygon', 
                            'coordinates': 
                                [[(0.0, 0.0), 
                                  (0.0, 1.0), 
                                  (1.0, 1.0), 
                                  (1.0, 0.0), 
                                  (0.0, 0.0)]] },
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        self.assertEqual(
            sorted(g['geometry'].items()),
            [('coordinates', [[(0.0, 0.0), 
                                  (0.0, 1.0), 
                                  (1.0, 1.0), 
                                  (1.0, 0.0), 
                                  (0.0, 0.0)]]), 
             ('type', 'Polygon')])
    def test_properties(self):
        f = { 'id': '1', 
              'geometry': { 'type': 'Polygon', 
                            'coordinates': 
                                [[(0.0, 0.0), 
                                  (0.0, 1.0), 
                                  (1.0, 1.0), 
                                  (1.0, 0.0), 
                                  (0.0, 0.0)]] },
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        self.assertEqual(g['properties']['title'], 'foo')


def test_feature_null_field(tmpdir):
    """
    In GDAL 2.2 the behaviour of OGR_F_IsFieldSet slightly changed.
    See GH #460.
    """
    meta = {"driver": "ESRI Shapefile", "schema": {"geometry": "Point", "properties": {"RETURN_P": "int"}}}
    filename = str(tmpdir.join("test_null.shp"))
    with fiona.open(filename, "w", **meta) as dst:
        g = {"coordinates": [1.0, 2.0], "type": "Point"}
        feature = {"geometry": g, "properties": {"RETURN_P": None}}
        dst.write(feature)

    with fiona.open(filename, "r") as src:
        feature = next(iter(src))
        assert(feature["properties"]["RETURN_P"] is None)
