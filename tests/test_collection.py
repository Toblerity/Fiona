# Testing collections and workspaces

import logging
import os
import sys
import types
import unittest

from shapely.geometry import asShape, mapping

from fiona import collection

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class ShapefileCollectionTest(unittest.TestCase):
    def test_io(self):
        c = collection("docs/data/test_uk.shp", "r")
        self.failUnlessEqual(c.name, "test_uk")
        self.failUnlessEqual(c.mode, "r")
        self.failUnlessEqual(c.opened, True)
        self.assertRaises(IOError, c.open)
        self.failUnless(iter(c))
        c.close()
        self.assertRaises(ValueError, iter, c)
        self.failUnlessEqual(c.opened, False)
        self.assertRaises(IOError, c.close)
    def test_len(self):
        c = collection("docs/data/test_uk.shp", "r")
        self.failUnlessEqual(len(c), 48)
    def test_schema(self):
        c = collection("docs/data/test_uk.shp", "r")
        s = c.schema['properties']
        self.failUnlessEqual(s['CAT'], "float")
        self.failUnlessEqual(s['FIPS_CNTRY'], "str")
    def test_context(self):
        with collection("docs/data/test_uk.shp", "r") as c:
            self.failUnlessEqual(c.name, "test_uk")
            self.failUnlessEqual(c.opened, True)
            self.failUnlessEqual(len(c), 48)
        self.failUnlessEqual(c.opened, False)
    def test_iter_one(self):
        with collection("docs/data/test_uk.shp", "r") as c:
            f = iter(c).next()
            self.failUnlessEqual(f['id'], "0")
            self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')
    def test_iter_one(self):
        with collection("docs/data/test_uk.shp", "r") as c:
            f = iter(c).next()
            self.failUnlessEqual(f['id'], "0")
            self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')
    def test_iter_list(self):
        with collection("docs/data/test_uk.shp", "r") as c:
            f = list(c)[0]
            self.failUnlessEqual(f['id'], "0")
            self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')
    def test_iter_all(self):
        with collection("docs/data/test_uk.shp", "r") as c:
            f = list(c.all)[0]
            self.failUnlessEqual(f['id'], "0")
            self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')
    def test_filter_1(self):
        with collection("docs/data/test_uk.shp", "r") as c:
            results = list(c.filter(bbox=(-15.0, 35.0, 15.0, 65.0)))
            self.failUnlessEqual(len(results), 48)
            f = results[0]
            self.failUnlessEqual(f['id'], "0")
            self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')
    def test_filter_1(self):
        with collection("docs/data/test_uk.shp", "r") as c:
            results = list(c.filter(bbox=(-15.0, 35.0, 15.0, 65.0)))
            self.failUnlessEqual(len(results), 48)
            f = results[0]
            self.failUnlessEqual(f['id'], "0")
            self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')

class ShapefileWriteCollectionTest(unittest.TestCase):
    def test_write(self):
        
        with collection("docs/data/test_uk.shp", "r") as input:
            
            schema = input.schema.copy()
            schema['geometry'] = 'Point'
            
            with collection(
                "test_write.shp", "w", "ESRI Shapefile", schema
                ) as output:

                    for f in input.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
                        
                        # geoprocessing
                        f['geometry'] = mapping(asShape(f['geometry']).centroid)
                        
                        output.write(f)

