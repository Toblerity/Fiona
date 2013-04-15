# Testing collections and workspaces

import logging
import os
import shutil
import sys
import unittest

import fiona
from fiona.collection import supported_drivers
from fiona.errors import FionaValueError, DriverError, SchemaError, CRSError

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class SupportedDriversTest(unittest.TestCase):
    def test_shapefile(self):
        self.failUnless("ESRI Shapefile" in supported_drivers)
        self.failUnlessEqual(
            set(supported_drivers["ESRI Shapefile"]), set("raw") )
    def test_map(self):
        self.failUnless("MapInfo File" in supported_drivers)
        self.failUnlessEqual(
            set(supported_drivers["MapInfo File"]), set("raw") )


class ReadingTest(unittest.TestCase):
    
    def setUp(self):
        self.c = fiona.open("docs/data/test_uk.shp", "r")
    
    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.failUnlessEqual(
            repr(self.c),
            ("<open Collection 'docs/data/test_uk.shp:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        self.c.close()
        self.failUnlessEqual(
            repr(self.c),
            ("<closed Collection 'docs/data/test_uk.shp:test_uk', mode 'r' "
            "at %s>" % hex(id(self.c))))

    def test_path(self):
        self.failUnlessEqual(self.c.path, "docs/data/test_uk.shp")

    def test_name(self):
        self.failUnlessEqual(self.c.name, "test_uk")
    
    def test_mode(self):
        self.failUnlessEqual(self.c.mode, "r")

    def test_collection(self):
        self.failUnlessEqual(self.c.encoding, "iso-8859-1")

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
        self.failUnlessEqual(self.c.driver, None)

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
        self.failUnlessEqual(crs['datum'], 'WGS84')
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
            ['datum', 'no_defs', 'proj'])

    def test_meta(self):
        self.failUnlessEqual(
            sorted(self.c.meta.keys()), ['crs', 'driver', 'schema'])

    def test_bounds(self):
        self.failUnlessAlmostEqual(self.c.bounds[0], -8.621389, 6)
        self.failUnlessAlmostEqual(self.c.bounds[1], 49.911659, 6)
        self.failUnlessAlmostEqual(self.c.bounds[2], 1.749444, 6)
        self.failUnlessAlmostEqual(self.c.bounds[3], 60.844444, 6)

    def test_context(self):
        with fiona.open("docs/data/test_uk.shp", "r") as c:
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

class UnsupportedDriverTest(unittest.TestCase):
    
    def test_immediate_fail_driver(self):
        schema = {
            'geometry': 'Point', 
            'properties': {'label': 'str', u'verit\xe9': 'int'} }
        self.assertRaises(
            DriverError, 
            fiona.open, "/tmp/foo", "w", "FileGDB", schema=schema)

# The file writing tests below presume we can write to /tmp.

class GenericWritingTest(unittest.TestCase):

    def setUp(self):
        schema = {
            'geometry': 'Point', 
            'properties': {'label': 'str', u'verit\xe9': 'int'} }
        self.c = fiona.open(
                "test-no-iter.shp", 
                "w", 
                "ESRI Shapefile", 
                schema=schema,
                encoding='Windows-1252')

    def tearDown(self):
        self.c.close()

    def test_encoding(self):
        self.assertEquals(self.c.encoding, 'Windows-1252')

    def test_no_iter(self):
        self.assertRaises(IOError, iter, self.c)

    def test_no_filter(self):
        self.assertRaises(IOError, self.c.filter)

class PointWritingTest(unittest.TestCase):

    def setUp(self):
        self.sink = fiona.open(
            "/tmp/point_writing_test.shp",
            "w",
            driver="ESRI Shapefile",
            schema={
                'geometry': 'Point', 
                'properties': {'title': 'str', 'date': 'date'}},
            crs={'init': "epsg:4326", 'no_defs': True},
            encoding='utf-8')

    def tearDown(self):
        self.sink.close()

    def test_cpg(self):
        """Requires GDAL 1.9"""
        self.sink.close()
        self.failUnless(open("/tmp/point_writing_test.cpg").readline() == 'UTF-8')

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

    def test_validate_record(self):
        fvalid = {
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': {'title': 'point one', 'date': "2012-01-29"}}
        finvalid = {
            'geometry': {'type': 'Point', 'coordinates': (0.0, -0.1)},
            'properties': {'not-a-title': 'point two', 'date': "2012-01-29"}}
        self.assertTrue(self.sink.validate_record(fvalid))
        self.assertFalse(self.sink.validate_record(finvalid))

class LineWritingTest(unittest.TestCase):

    def setUp(self):
        self.sink = fiona.open(
            "/tmp/line_writing_test.shp",
            "w",
            driver="ESRI Shapefile",
            schema={
                'geometry': 'LineString', 
                'properties': {'title': 'str', 'date': 'date'}},
            crs={'init': "epsg:4326", 'no_defs': True})

    def tearDown(self):
        self.sink.close()

    def test_write_one(self):
        self.failUnlessEqual(len(self.sink), 0)
        self.failUnlessEqual(self.sink.bounds, (0.0, 0.0, 0.0, 0.0))
        f = {
            'geometry': {'type': 'LineString', 
                         'coordinates': [(0.0, 0.1), (0.0, 0.2)]},
            'properties': {'title': 'line one', 'date': "2012-01-29"}}
        self.sink.writerecords([f])
        self.failUnlessEqual(len(self.sink), 1)
        self.failUnlessEqual(self.sink.bounds, (0.0, 0.1, 0.0, 0.2))

    def test_write_two(self):
        self.failUnlessEqual(len(self.sink), 0)
        self.failUnlessEqual(self.sink.bounds, (0.0, 0.0, 0.0, 0.0))
        f1 = {
            'geometry': {'type': 'LineString', 
                         'coordinates': [(0.0, 0.1), (0.0, 0.2)]},
            'properties': {'title': 'line one', 'date': "2012-01-29"}}
        f2 = {
            'geometry': {'type': 'MultiLineString', 
                         'coordinates': [
                            [(0.0, 0.0), (0.0, -0.1)], 
                            [(0.0, -0.1), (0.0, -0.2)] ]},
            'properties': {'title': 'line two', 'date': "2012-01-29"}}
        self.sink.writerecords([f1, f2])
        self.failUnlessEqual(len(self.sink), 2)
        self.failUnlessEqual(self.sink.bounds, (0.0, -0.2, 0.0, 0.2))

class PointAppendTest(unittest.TestCase):
    # Tests 3D shapefiles too
    def setUp(self):
        os.mkdir("test_append_point")
        with fiona.open("docs/data/test_uk.shp", "r") as input:
            output_schema = input.schema.copy()
            output_schema['geometry'] = '3D Point'
            with fiona.open(
                    "test_append_point/" + "test_append_point.shp", 
                    "w", crs=None, driver="ESRI Shapefile", schema=output_schema
                    ) as output:
                for f in input.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
                    f['geometry'] = {
                        'type': 'Point',
                        'coordinates': f['geometry']['coordinates'][0][0] }
                    output.write(f)

    def tearDown(self):
        shutil.rmtree("test_append_point")

    def test_append_point(self):
        with fiona.open("test_append_point/test_append_point.shp", "a") as c:
            self.assertEqual(c.schema['geometry'], '3D Point')
            c.write({'geometry': {'type': 'Point', 'coordinates': (0.0, 45.0)},
                     'properties': { 'FIPS_CNTRY': 'UK', 
                                     'AREA': 0.0, 
                                     'CAT': 1.0, 
                                     'POP_CNTRY': 0, 
                                     'CNTRY_NAME': u'Foo'} })
            self.assertEqual(len(c), 8)

class LineAppendTest(unittest.TestCase):

    def setUp(self):
        os.mkdir("test_append_line")
        with fiona.open(
                "test_append_line/" + "test_append_line.shp",
                "w",
                driver="ESRI Shapefile",
                schema={
                    'geometry': 'MultiLineString', 
                    'properties': {'title': 'str', 'date': 'date'}},
                crs={'init': "epsg:4326", 'no_defs': True}) as output:
            f = {'geometry': {'type': 'MultiLineString', 
                              'coordinates': [[(0.0, 0.1), (0.0, 0.2)]]},
                'properties': {'title': 'line one', 'date': "2012-01-29"}}
            output.writerecords([f])

    def tearDown(self):
        shutil.rmtree("test_append_line")

    def test_append_line(self):
        with fiona.open("test_append_line/test_append_line.shp", "a") as c:
            self.assertEqual(c.schema['geometry'], 'LineString')
            f1 = {
                'geometry': {'type': 'LineString', 
                             'coordinates': [(0.0, 0.1), (0.0, 0.2)]},
                'properties': {'title': 'line one', 'date': "2012-01-29"}}
            f2 = {
                'geometry': {'type': 'MultiLineString', 
                             'coordinates': [
                                [(0.0, 0.0), (0.0, -0.1)], 
                                [(0.0, -0.1), (0.0, -0.2)] ]},
                'properties': {'title': 'line two', 'date': "2012-01-29"}}
            c.writerecords([f1, f2])
            self.failUnlessEqual(len(c), 3)
            self.failUnlessEqual(c.bounds, (0.0, -0.2, 0.0, 0.2))

class ShapefileFieldWidthTest(unittest.TestCase):
    
    def test_text(self):
        with fiona.open("/tmp/textfield.shp", "w",
                driver="ESRI Shapefile",
                schema={'geometry': 'Point', 'properties': {'text': 'str:255'}}
                ) as c:
            c.write(
                {'geometry': {'type': 'Point', 'coordinates': (0.0, 45.0)},
                 'properties': { 'text': 'a' * 255 }})
        c = fiona.open("/tmp/textfield.shp", "r")
        self.failUnlessEqual(c.schema['properties']['text'], 'str:255')
        f = next(iter(c))
        self.failUnlessEqual(f['properties']['text'], 'a' * 255)
        c.close()


class CollectionTest(unittest.TestCase):

    def test_invalid_mode(self):
        self.assertRaises(ValueError, fiona.open, "/tmp/bogus.shp", "r+")

    def test_w_args(self):
        self.assertRaises(FionaValueError, fiona.open, "test-no-iter.shp", "w")
        self.assertRaises(
            FionaValueError, fiona.open, "test-no-iter.shp", "w", "Driver")

    def test_no_path(self):
        self.assertRaises(IOError, fiona.open, "no-path.shp", "a")

    def test_no_read_conn_str(self):
        self.assertRaises(IOError, fiona.open, "PG:dbname=databasename", "r")

    def test_no_read_directory(self):
        self.assertRaises(ValueError, fiona.open, ".", "r")


