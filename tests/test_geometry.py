# testing geometry extension, to be called by nosetests

import unittest

from fiona.geometry import CoordSequence, geometry_wkb

class CoordSequenceTest(unittest.TestCase):
    def test_cseq(self):
        coords = [(0.0, 0.0), (1.0, 1.0)]
        x, y = zip(*coords)
        cs = CoordSequence(x, y)
        self.failUnlessEqual(tuple(cs.x), x)
        self.failUnlessEqual(tuple(cs.y), y)

class LineStringTest(unittest.TestCase):
    def test_line(self):
        # Hex-encoded LineString (0 0, 1 1)
        wkb = "01020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom.type, "LineString")
        self.failUnlessEqual(geom.coordinates, [(0.0, 0.0), (1.0, 1.0)])
        self.failUnlessEqual(geom.mapping()['type'], "LineString")
        self.failUnlessEqual(geom.mapping()['coordinates'], [(0.0, 0.0), (1.0, 1.0)])
class MultiPointTest(unittest.TestCase):
    def test_multipoint(self):
        wkb = "0104000000020000000101000000000000000000000000000000000000000101000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.failUnlessEqual(geom.type, "MultiPoint")
        self.failUnlessEqual(geom.coordinates, [(0.0, 0.0), (1.0, 1.0)])
        self.failUnlessEqual(geom.mapping()['type'], "MultiPoint")
        self.failUnlessEqual(geom.mapping()['coordinates'], [(0.0, 0.0), (1.0, 1.0)])
