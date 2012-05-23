# testing features, to be called by nosetests

import logging
import sys
import unittest

from fiona import collection
from fiona.collection import Collection
from fiona.ogrext import featureRT

#logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class PointRoundTripTest(unittest.TestCase):
    def setUp(self):
        schema = {'geometry': 'Point', 'properties': {'title': 'str'}}
        self.c = Collection(
            "/tmp/foo.shp", "w", driver="ESRI Shapefile", schema=schema)
    def test_geometry(self):
        f = { 'id': '1', 
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        self.failUnlessEqual(
            sorted(g['geometry'].items()),
            [('coordinates', (0.0, 0.0)), ('type', 'Point')])
    def test_properties(self):
        f = { 'id': '1', 
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        self.failUnlessEqual(g['properties']['title'], 'foo')
    def test_none_property(self):
        f = { 'id': '1',
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': None} }
        g = featureRT(f, self.c)
        self.failUnlessEqual(g['properties']['title'], None)

class LineStringRoundTripTest(unittest.TestCase):
    def setUp(self):
        schema = {'geometry': 'LineString', 'properties': {'title': 'str'}}
        self.c = Collection(
            "/tmp/foo.shp", "w", "ESRI Shapefile", schema=schema)
    def test_geometry(self):
        f = { 'id': '1', 
              'geometry': { 'type': 'LineString', 
                            'coordinates': [(0.0, 0.0), (1.0, 1.0)] },
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        self.failUnlessEqual(
            sorted(g['geometry'].items()),
            [('coordinates', [(0.0, 0.0), (1.0, 1.0)]), 
             ('type', 'LineString')])
    def test_properties(self):
        f = { 'id': '1',
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        self.failUnlessEqual(g['properties']['title'], 'foo')

class PolygonRoundTripTest(unittest.TestCase):
    def setUp(self):
        schema = {'geometry': 'Polygon', 'properties': {'title': 'str'}}
        self.c = Collection(
            "/tmp/foo.shp", "w", "ESRI Shapefile", schema=schema)
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
        self.failUnlessEqual(
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
        self.failUnlessEqual(g['properties']['title'], 'foo')

