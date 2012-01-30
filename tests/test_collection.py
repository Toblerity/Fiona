# Testing collections and workspaces

import logging
import os
import shutil
import sys
import unittest

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

    def test_driver(self):
        c = collection("docs/data/test_uk.shp", "r")
        self.failUnlessEqual(c.driver, "ESRI Shapefile")

    def test_schema(self):
        c = collection("docs/data/test_uk.shp", "r")
        s = c.schema['properties']
        self.failUnlessEqual(s['CAT'], "float")
        self.failUnlessEqual(s['FIPS_CNTRY'], "str")

    def test_crs(self):
        c = collection("docs/data/test_uk.shp", "r")
        self.failUnlessEqual(c.crs['ellps'], 'WGS84')
        self.failUnless(c.crs['no_defs'])

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

    def test_no_write(self):
        with collection("docs/data/test_uk.shp", "r") as c:
            self.assertRaises(IOError, c.write, {})


class ShapefileWriteCollectionTest(unittest.TestCase):
    
    def test_no_read(self):
        schema = {'geometry': 'Point', 'properties': {'label': 'str'}}
        with collection(
                "test-no-iter.shp", "w", "ESRI Shapefile", schema=schema) as c:
            self.assertRaises(IOError, iter, c)
            self.assertRaises(IOError, c.filter)

    def test_write_point(self):
        with collection("docs/data/test_uk.shp", "r") as input:
            schema = input.schema.copy()
            schema['geometry'] = 'Point'
            with collection(
                    "test_write_point.shp", "w", "ESRI Shapefile", schema
                    ) as output:
                for f in input.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
                    f['geometry'] = {
                        'type': 'Point',
                        'coordinates': f['geometry']['coordinates'][0][0] }
                    output.write(f)

    def test_write_polygon_with_crs(self):
        with collection("docs/data/test_uk.shp", "r") as input:
            schema = input.schema.copy()
            with collection(
                    "test_write_polygon.shp", "w", "ESRI Shapefile",
                    schema=schema, crs={'init': "epsg:4326", 'no_defs': True}
                    ) as output:
                for f in input:
                    output.write(f)

class ShapefileWriteWithDateCollectionTest(unittest.TestCase):
    
    def test_write_point_wdate(self):
        with collection("docs/data/test_uk.shp", "r") as input:
            schema = input.schema.copy()
            schema['geometry'] = 'Point'
            schema['properties']['date'] = 'date'
            with collection(
                    "test_write_date.shp", "w", "ESRI Shapefile", schema
                    ) as output:
                for f in input.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
                    f['geometry'] = {
                        'type': 'Point',
                        'coordinates': f['geometry']['coordinates'][0][0] }
                    f['properties']['date'] = "2012-01-29"
                    output.write(f)

class ShapefileAppendTest(unittest.TestCase):

    def setUp(self):
        os.mkdir("append-test")
        with collection("docs/data/test_uk.shp", "r") as input:
            schema = input.schema.copy()
            schema['geometry'] = 'Point'
            with collection(
                    "append-test/" + "test_append_point.shp", 
                    "w", "ESRI Shapefile", schema
                    ) as output:
                for f in input.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
                    f['geometry'] = {
                        'type': 'Point',
                        'coordinates': f['geometry']['coordinates'][0][0] }
                    output.write(f)

    def tearDown(self):
        shutil.rmtree("append-test")

    def test_append_point(self):
        with collection("append-test/test_append_point.shp", "a") as c:
            self.assertEqual(c.schema['geometry'], 'Point')
            c.write({'geometry': {'type': 'Point', 'coordinates': (0.0, 45.0)},
                     'properties': {'FIPS_CNTRY': 'UK'}})
            self.assertEqual(len(c), 8)

class CollectionTest(unittest.TestCase):

    def test_invalid_mode(self):
        self.assertRaises(ValueError, collection, "/tmp/bogus.shp", "r+")

    def test_w_args(self):
        self.assertRaises(ValueError, collection, "test-no-iter.shp", "w")
        self.assertRaises(ValueError, collection, "test-no-iter.shp", "w", "Driver")

    def test_no_path(self):
        self.assertRaises(OSError, collection, "no-path.shp", "a")

    def test_no_read_conn_str(self):
        self.assertRaises(OSError, collection, "PG:dbname=databasename", "r")

    def test_no_read_directory(self):
        self.assertRaises(ValueError, collection, ".", "r")


