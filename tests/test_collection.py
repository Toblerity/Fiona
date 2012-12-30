# Testing collections and workspaces

import logging
import os
import shutil
import sys
import unittest

from fiona import collection

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class ReadingTest(unittest.TestCase):
    
    def setUp(self):
        self.c = collection("docs/data/test_uk.shp", "r")
    
    def tearDown(self):
        self.c.close()
    
    def test_name(self):
        self.failUnlessEqual(self.c.name, "test_uk")
    
    def test_mode(self):
        self.failUnlessEqual(self.c.mode, "r")
    
    def test_iter(self):
        self.failUnless(iter(self.c))
    
    def test_closed_no_iter(self):
        self.c.close()
        self.assertRaises(ValueError, iter, self.c)

    def test_len(self):
        self.failUnlessEqual(len(self.c), 48)
    
    def test_closed_len(self):
        # Len is lazy, it's never computed in this case. TODO?
        self.c.close()
        self.failUnlessEqual(len(self.c), 0)

    def test_len_closed_len(self):
        # Lazy len is computed in this case and sticks.
        len(self.c)
        self.c.close()
        self.failUnlessEqual(len(self.c), 48)
    
    def test_driver(self):
        self.failUnlessEqual(self.c.driver, "ESRI Shapefile")
    
    def test_closed_driver(self):
        self.c.close()
        self.failUnlessEqual(self.c.driver, "ESRI Shapefile")

    def test_driver_closed_driver(self):
        self.c.driver
        self.c.close()
        self.failUnlessEqual(self.c.driver, "ESRI Shapefile")
    
    def test_schema(self):
        s = self.c.schema['properties']
        self.failUnlessEqual(s['CAT'], "float")
        self.failUnlessEqual(s['FIPS_CNTRY'], "str")

    def test_closed_schema(self):
        # Schema is lazy too, never computed in this case. TODO?
        self.c.close()
        self.failUnlessEqual(self.c.schema, None)

    def test_schema_closed_schema(self):
        self.c.schema
        self.c.close()
        self.failUnlessEqual(
            sorted(self.c.schema.keys()),
            ['geometry', 'properties'])

    def test_crs(self):
        crs = self.c.crs
        self.failUnlessEqual(crs['ellps'], 'WGS84')
        self.failUnless(crs['no_defs'])

    def test_closed_crs(self):
        # Crs is lazy too, never computed in this case. TODO?
        self.c.close()
        self.failUnlessEqual(self.c.crs, None)

    def test_crs_closed_crs(self):
        self.c.crs
        self.c.close()
        self.failUnlessEqual(
            sorted(self.c.crs.keys()),
            ['datum', 'ellps', 'no_defs', 'proj'])

    def test_bounds(self):
        self.failUnlessAlmostEqual(self.c.bounds[0], -8.621389, 6)
        self.failUnlessAlmostEqual(self.c.bounds[1], 49.911659, 6)
        self.failUnlessAlmostEqual(self.c.bounds[2], 1.749444, 6)
        self.failUnlessAlmostEqual(self.c.bounds[3], 60.844444, 6)

    def test_context(self):
        with collection("docs/data/test_uk.shp", "r") as c:
            self.failUnlessEqual(c.name, "test_uk")
            self.failUnlessEqual(len(c), 48)
        self.failUnlessEqual(c.closed, True)

    def test_iter_one(self):
        f = iter(self.c).next()
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')

    def test_iter_list(self):
        f = list(self.c)[0]
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')

    def test_filter_1(self):
        results = list(self.c.filter(bbox=(-15.0, 35.0, 15.0, 65.0)))
        self.failUnlessEqual(len(results), 48)
        f = results[0]
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')

    def test_no_write(self):
        self.assertRaises(IOError, self.c.write, {})

# The file writing tests below presume we can write to /tmp.

class GenericWritingTest(unittest.TestCase):

    def setUp(self):
        schema = {
            'geometry': 'Point', 
            'properties': {'label': 'str', u'verit\xe9': 'int'} }
        self.c = collection(
                "test-no-iter.shp", 
                "w", 
                "ESRI Shapefile", 
                schema=schema)

    def tearDown(self):
        self.c.close()

    def test_no_iter(self):
        self.assertRaises(IOError, iter, self.c)

    def test_no_filter(self):
        self.assertRaises(IOError, self.c.filter)

class PointWritingTest(unittest.TestCase):

    def setUp(self):
        self.sink = collection(
            "/tmp/point_writing_test.shp",
            "w",
            driver="ESRI Shapefile",
            schema={
                'geometry': 'Point', 
                'properties': {'title': 'str', 'date': 'date'}},
            crs={'init': "epsg:4326", 'no_defs': True})

    def tearDown(self):
        self.sink.close()

    def test_write_one(self):
        self.failUnlessEqual(len(self.sink), 0)
        self.failUnlessEqual(self.sink.bounds, (0.0, 0.0, 0.0, 0.0))
        f = {
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': {'title': 'point one', 'date': "2012-01-29"}}
        self.sink.writerecords([f])
        self.failUnlessEqual(len(self.sink), 1)
        self.failUnlessEqual(self.sink.bounds, (0.0, 0.1, 0.0, 0.1))

    def test_write_two(self):
        self.failUnlessEqual(len(self.sink), 0)
        self.failUnlessEqual(self.sink.bounds, (0.0, 0.0, 0.0, 0.0))
        f1 = {
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': {'title': 'point one', 'date': "2012-01-29"}}
        f2 = {
            'geometry': {'type': 'Point', 'coordinates': (0.0, -0.1)},
            'properties': {'title': 'point two', 'date': "2012-01-29"}}
        self.sink.writerecords([f1, f2])
        self.failUnlessEqual(len(self.sink), 2)
        self.failUnlessEqual(self.sink.bounds, (0.0, -0.1, 0.0, 0.1))

class AppendingTest(unittest.TestCase):

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


