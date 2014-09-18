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

# The round tripping tests are defined in this not to be run base class.
#
class RoundTripping(object):
    """Derive type specific classes from this."""
    def test_type(self):
        self.failUnlessEqual(
            geometryRT(self.geom)['type'], self.geom['type'])
    def test_coordinates(self):
        self.failUnlessEqual(
            geometryRT(self.geom)['coordinates'], self.geom['coordinates'])

# All these get their tests from the RoundTripping class.
#
class PointRoundTripTest(unittest.TestCase, RoundTripping):
    def setUp(self):
        self.geom = {'type': "Point", 'coordinates': (0.0, 0.0)}

class LineStringRoundTripTest(unittest.TestCase, RoundTripping):
    def setUp(self):
        self.geom = {
            'type': "LineString", 
            'coordinates': [(0.0, 0.0), (1.0, 1.0)]}

class PolygonRoundTripTest1(unittest.TestCase, RoundTripping):
    """An explicitly closed polygon."""
    def setUp(self):
        self.geom = {
            'type': "Polygon", 
            'coordinates': [
                [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]]}

class PolygonRoundTripTest2(unittest.TestCase, RoundTripping):
    """An implicitly closed polygon."""
    def setUp(self):
        self.geom = {
            'type': "Polygon", 
            'coordinates': [
                [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]]}
    def test_coordinates(self):
        self.failUnlessEqual(
            [geometryRT(self.geom)['coordinates'][0][:-1]], 
            self.geom['coordinates'])

class MultiPointRoundTripTest(unittest.TestCase, RoundTripping):
    def setUp(self):
        self.geom = {
            'type': "MultiPoint", 'coordinates': [(0.0, 0.0), (1.0, 1.0)]}

class MultiLineStringRoundTripTest(unittest.TestCase, RoundTripping):
    def setUp(self):
        self.geom = {
            'type': "MultiLineString", 
            'coordinates': [[(0.0, 0.0), (1.0, 1.0)]]}

class MultiPolygonRoundTripTest1(unittest.TestCase, RoundTripping):
    def setUp(self):
        # This is an explicitly closed polygon.
        self.geom = {
            'type': "MultiPolygon", 
            'coordinates': [[
                [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]
                ]]}

class MultiPolygonRoundTripTest2(unittest.TestCase, RoundTripping):
    def setUp(self):
        # This is an implicitly closed polygon.
        self.geom = {
            'type': "MultiPolygon", 
            'coordinates': 
                [[[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]]]}
    def test_coordinates(self):
        self.failUnlessEqual(
            [[geometryRT(self.geom)['coordinates'][0][0][:-1]]], 
            self.geom['coordinates'])

class GeometryCollectionRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.geom = {
            'type': "GeometryCollection",
            'geometries': [
                {'type': "Point", 'coordinates': (0.0, 0.0)}, {
                    'type': "LineString", 
                    'coordinates': [(0.0, 0.0), (1.0, 1.0)]}]}
    def test_len(self):
        result = geometryRT(self.geom)
        self.failUnlessEqual(len(result['geometries']), 2)
    def test_type(self):
        result = geometryRT(self.geom)
        self.failUnlessEqual(
            [g['type'] for g in result['geometries']], 
            ['Point', 'LineString'])

class PointTest(unittest.TestCase):
    def test_point(self):
        # Hex-encoded Point (0 0)
        try:
            wkb = bytes.fromhex("010100000000000000000000000000000000000000")
        except:
            wkb = "010100000000000000000000000000000000000000".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom['type'], "Point")
        self.failUnlessEqual(geom['coordinates'], (0.0, 0.0))

class LineStringTest(unittest.TestCase):
    def test_line(self):
        # Hex-encoded LineString (0 0, 1 1)
        try:
            wkb = bytes.fromhex("01020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f")
        except:
            wkb = "01020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom['type'], "LineString")
        self.failUnlessEqual(geom['coordinates'], [(0.0, 0.0), (1.0, 1.0)])

class PolygonTest(unittest.TestCase):
    def test_polygon(self):
        # 1 x 1 box (0, 0, 1, 1)
        try:
            wkb = bytes.fromhex("01030000000100000005000000000000000000f03f0000000000000000000000000000f03f000000000000f03f0000000000000000000000000000f03f00000000000000000000000000000000000000000000f03f0000000000000000")
        except:
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
        try:
            wkb = bytes.fromhex("0104000000020000000101000000000000000000000000000000000000000101000000000000000000f03f000000000000f03f")
        except:
            wkb = "0104000000020000000101000000000000000000000000000000000000000101000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom['type'], "MultiPoint")
        self.failUnlessEqual(geom['coordinates'], [(0.0, 0.0), (1.0, 1.0)])

class MultiLineStringTest(unittest.TestCase):
    def test_multilinestring(self):
        # Hex-encoded LineString (0 0, 1 1)
        try:
            wkb = bytes.fromhex("01050000000100000001020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f")
        except:
            wkb = "01050000000100000001020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom['type'], "MultiLineString")
        self.failUnlessEqual(len(geom['coordinates']), 1)
        self.failUnlessEqual(len(geom['coordinates'][0]), 2)
        self.failUnlessEqual(geom['coordinates'][0], [(0.0, 0.0), (1.0, 1.0)])

class MultiPolygonTest(unittest.TestCase):
    def test_multipolygon(self):
        # [1 x 1 box (0, 0, 1, 1)]
        try:
            wkb = bytes.fromhex("01060000000100000001030000000100000005000000000000000000f03f0000000000000000000000000000f03f000000000000f03f0000000000000000000000000000f03f00000000000000000000000000000000000000000000f03f0000000000000000")
        except:
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

