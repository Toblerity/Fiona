# testing features, to be called by nosetests

import unittest

from fiona.feature import Feature

class FeatureTest(unittest.TestCase):
    def test_feature_init(self):
        f = Feature('1', {'foo': 'bar'}, [0.0, 0.0])
        self.failUnlessEqual(f.id, '1')
        self.failUnlessEqual(f.properties, {'foo': 'bar'})
        self.failUnlessEqual(f.geometry,  [0.0, 0.0])

