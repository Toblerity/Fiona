# testing features, to be called by nosetests

import unittest

from fiona.feature import Feature, Geometry, Part

class PartTest(unittest.TestCase):
    def test_empty_part(self):
        p = Part()
        self.failUnlessEqual(p.xs, None)
        self.failUnlessEqual(p.xs, None)
    def test_part_line(self):
        p = Part([(0, 0), (1, 1)])
        self.failUnlessEqual(list(p.xs), [0.0, 1.0])
        self.failUnlessEqual(list(p.ys), [0.0, 1.0])

class GeometryTest(unittest.TestCase):
    def test_empty_geometry(self):
        g = Geometry()
        self.failUnlessEqual(g.parts, [])

class FeatureTest(unittest.TestCase):
    def test_feature_init(self):
        f = Feature('1', {'foo': 'bar'}, [0.0, 0.0])
        self.failUnlessEqual(f.id, '1')
        self.failUnlessEqual(f.properties, {'foo': 'bar'})
        self.failUnlessEqual(f.geometry,  [0.0, 0.0])

