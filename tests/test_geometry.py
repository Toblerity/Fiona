# testing geometry extension, to be called by nosetests

import logging
import sys
import unittest

from fiona.ogrext import GeomBuilder, geometryRT

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

def geometry_wkb(wkb):
    return GeomBuilder().build_wkb(wkb)


class OGRBuilderExceptionsTest(unittest.TestCase):
    def test(self):
        geom = {'type': "Bogus", 'coordinates': None}
        self.assertRaises(ValueError, geometryRT, geom)

class PointRoundTripTest(unittest.TestCase):
    def test(self):
        geom = {'type': "Point", 'coordinates': (0.0, 0.0)}
        result = geometryRT(geom)
        self.failUnlessEqual(result['type'], "Point")
        self.failUnlessEqual(result['coordinates'], (0.0, 0.0))

class LineStringRoundTripTest(unittest.TestCase):
    def test(self):
        geom = {'type': "LineString", 'coordinates': [(0.0, 0.0), (1.0, 1.0)]}
        result = geometryRT(geom)
        self.failUnlessEqual(result['type'], "LineString")
        self.failUnlessEqual(result['coordinates'], [(0.0, 0.0), (1.0, 1.0)])

class PolygonRoundTripTest(unittest.TestCase):
    def test(self):
        geom = {'type': "Polygon", 
                'coordinates': [[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]]}
        result = geometryRT(geom)
        self.failUnlessEqual(result['type'], "Polygon")
        self.failUnlessEqual(
            result['coordinates'], 
            [[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]] )

class MultiPointRoundTripTest(unittest.TestCase):
    def test(self):
        geom = {'type': "MultiPoint", 'coordinates': [(0.0, 0.0), (1.0, 1.0)]}
        result = geometryRT(geom)
        self.failUnlessEqual(result['type'], "MultiPoint")
        self.failUnlessEqual(result['coordinates'], [(0.0, 0.0), (1.0, 1.0)])

class MultiLineStringRoundTripTest(unittest.TestCase):
    def test(self):
        geom = {'type': "MultiLineString", 
                'coordinates': [[(0.0, 0.0), (1.0, 1.0)]]}
        result = geometryRT(geom)
        self.failUnlessEqual(result['type'], "MultiLineString")
        self.failUnlessEqual(result['coordinates'], [[(0.0, 0.0), (1.0, 1.0)]])

class MultiPolygonRoundTripTest(unittest.TestCase):
    def test(self):
        geom = {'type': "MultiPolygon", 
                'coordinates': [[[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]]]}
        result = geometryRT(geom)
        self.failUnlessEqual(result['type'], "MultiPolygon")
        self.failUnlessEqual(
            result['coordinates'], 
            [[[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]]] )

class GeometryCollectionRoundTripTest(unittest.TestCase):
    def test(self):
        geom = {'type': "GeometryCollection",
                'geometries': [
                    {'type': "Point", 'coordinates': (0.0, 0.0)},
                    {'type': "LineString", 'coordinates': [(0.0, 0.0), (1.0, 1.0)]}
                ]}
        result = geometryRT(geom)
        self.failUnlessEqual(len(result['geometries']), 2)
        self.failUnlessEqual(
            [g['type'] for g in result['geometries']], ['Point', 'LineString'] )


class PointTest(unittest.TestCase):
    def test_point(self):
        # Hex-encoded Point (0 0)
        wkb = "010100000000000000000000000000000000000000".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom['type'], "Point")
        self.failUnlessEqual(geom['coordinates'], (0.0, 0.0))

class LineStringTest(unittest.TestCase):
    def test_line(self):
        # Hex-encoded LineString (0 0, 1 1)
        wkb = "01020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom['type'], "LineString")
        self.failUnlessEqual(geom['coordinates'], [(0.0, 0.0), (1.0, 1.0)])

class PolygonTest(unittest.TestCase):
    def test_polygon(self):
        # 1 x 1 box (0, 0, 1, 1)
        wkb = "01030000000100000005000000000000000000f03f0000000000000000000000000000f03f000000000000f03f0000000000000000000000000000f03f00000000000000000000000000000000000000000000f03f0000000000000000".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom['type'], "Polygon")
        self.failUnlessEqual(len(geom['coordinates']), 1)
        self.failUnlessEqual(len(geom['coordinates'][0]), 5)
        x, y = zip(*geom['coordinates'][0])
        self.failUnlessEqual(min(x), 0.0)
        self.failUnlessEqual(min(y), 0.0)
        self.failUnlessEqual(max(x), 1.0)
        self.failUnlessEqual(max(y), 1.0)

class MultiPointTest(unittest.TestCase):
    def test_multipoint(self):
        wkb = "0104000000020000000101000000000000000000000000000000000000000101000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom['type'], "MultiPoint")
        self.failUnlessEqual(geom['coordinates'], [(0.0, 0.0), (1.0, 1.0)])

class MultiLineStringTest(unittest.TestCase):
    def test_multilinestring(self):
        # Hex-encoded LineString (0 0, 1 1)
        wkb = "01050000000100000001020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom['type'], "MultiLineString")
        self.failUnlessEqual(len(geom['coordinates']), 1)
        self.failUnlessEqual(len(geom['coordinates'][0]), 2)
        self.failUnlessEqual(geom['coordinates'][0], [(0.0, 0.0), (1.0, 1.0)])

class MultiPolygonTest(unittest.TestCase):
    def test_multipolygon(self):
        # [1 x 1 box (0, 0, 1, 1)]
        wkb = "01060000000100000001030000000100000005000000000000000000f03f0000000000000000000000000000f03f000000000000f03f0000000000000000000000000000f03f00000000000000000000000000000000000000000000f03f0000000000000000".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom['type'], "MultiPolygon")
        self.failUnlessEqual(len(geom['coordinates']), 1)
        self.failUnlessEqual(len(geom['coordinates'][0]), 1)
        self.failUnlessEqual(len(geom['coordinates'][0][0]), 5)
        x, y = zip(*geom['coordinates'][0][0])
        self.failUnlessEqual(min(x), 0.0)
        self.failUnlessEqual(min(y), 0.0)
        self.failUnlessEqual(max(x), 1.0)
        self.failUnlessEqual(max(y), 1.0)

