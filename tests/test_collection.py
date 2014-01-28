# Testing collections and workspaces

import logging
import os
import shutil
import sys
import subprocess
import unittest
import tempfile

import fiona
from fiona.collection import Collection, supported_drivers
from fiona.errors import FionaValueError, DriverError, SchemaError, CRSError

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

TEMPDIR = tempfile.gettempdir()

class SupportedDriversTest(unittest.TestCase):
    def test_shapefile(self):
        self.failUnless("ESRI Shapefile" in supported_drivers)
        self.failUnlessEqual(
            set(supported_drivers["ESRI Shapefile"]), set("raw") )
    def test_map(self):
        self.failUnless("MapInfo File" in supported_drivers)
        self.failUnlessEqual(
            set(supported_drivers["MapInfo File"]), set("raw") )

class CollectionArgsTest(unittest.TestCase):
    def test_path(self):
        self.assertRaises(TypeError, Collection, (0))
    def test_mode(self):
        self.assertRaises(TypeError, Collection, ("foo"), mode=0)
    def test_driver(self):
        self.assertRaises(TypeError, Collection, ("foo"), mode='w', driver=1)
    def test_schema(self):
        self.assertRaises(
            TypeError, Collection, ("foo"), mode='w', 
            driver="ESRI Shapefile", schema=1)
    def test_crs(self):
        self.assertRaises(
            TypeError, Collection, ("foo"), mode='w', 
            driver="ESRI Shapefile", schema=0, crs=1)
    def test_encoding(self):
        self.assertRaises(
            TypeError, Collection, ("foo"), mode='r', 
            encoding=1)
    def test_layer(self):
        self.assertRaises(
            TypeError, Collection, ("foo"), mode='r', 
            layer=0.5)
    def test_vsi(self):
        self.assertRaises(
            TypeError, Collection, ("foo"), mode='r', 
            vsi='git')
    def test_archive(self):
        self.assertRaises(
            TypeError, Collection, ("foo"), mode='r', 
            archive=1)
    def test_write_numeric_layer(self):
        self.assertRaises(ValueError, Collection, ("foo"), mode='w', layer=1)
    def test_write_geojson_layer(self):
        self.assertRaises(ValueError, Collection, ("foo"), mode='w', driver='GeoJSON', layer='foo')
    def test_append_geojson(self):
        self.assertRaises(ValueError, Collection, ("foo"), mode='w', driver='ARCGEN')

class OpenExceptionTest(unittest.TestCase):
    def test_no_archive(self):
        self.assertRaises(IOError, fiona.open, ("/"), mode='r', vfs="zip:///foo.zip")

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
        self.failUnlessEqual(self.c.path, 'docs/data/test_uk.shp')

    def test_name(self):
        self.failUnlessEqual(self.c.name, 'test_uk')
    
    def test_mode(self):
        self.failUnlessEqual(self.c.mode, 'r')

    def test_collection(self):
        self.failUnlessEqual(self.c.encoding, 'iso-8859-1')

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
        self.failUnlessEqual(s['CAT'], "float:16")
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
            sorted(self.c.meta.keys()), 
            ['crs', 'driver', 'schema'])

    def test_bounds(self):
        self.failUnlessAlmostEqual(self.c.bounds[0], -8.621389, 6)
        self.failUnlessAlmostEqual(self.c.bounds[1], 49.911659, 6)
        self.failUnlessAlmostEqual(self.c.bounds[2], 1.749444, 6)
        self.failUnlessAlmostEqual(self.c.bounds[3], 60.844444, 6)

    def test_context(self):
        with fiona.open("docs/data/test_uk.shp", "r") as c:
            self.failUnlessEqual(c.name, 'test_uk')
            self.failUnlessEqual(len(c), 48)
        self.failUnlessEqual(c.closed, True)

    def test_iter_one(self):
        itr = iter(self.c)
        f = next(itr)
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')

    def test_iter_list(self):
        f = list(self.c)[0]
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')

    def test_re_iter_list(self):
        f = list(self.c)[0] # Run through iterator
        f = list(self.c)[0] # Run through a new, reset iterator
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')

    def test_no_write(self):
        self.assertRaises(IOError, self.c.write, {})

class FilterReadingTest(unittest.TestCase):
    def setUp(self):
        self.c = fiona.open("docs/data/test_uk.shp", "r")
    def tearDown(self):
        self.c.close()
    def test_filter_1(self):
        results = list(self.c.filter(bbox=(-15.0, 35.0, 15.0, 65.0)))
        self.failUnlessEqual(len(results), 48)
        f = results[0]
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['FIPS_CNTRY'], 'UK')

class UnsupportedDriverTest(unittest.TestCase):
    
    def test_immediate_fail_driver(self):
        schema = {
            'geometry': 'Point', 
            'properties': {'label': 'str', u'verit\xe9': 'int'} }
        self.assertRaises(
            DriverError, 
            fiona.open, os.path.join(TEMPDIR, "foo"), "w", "Bogus", schema=schema)

class GenericWritingTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        schema = {
            'geometry': 'Point', 
            'properties': [('label', 'str'), (u'verit\xe9', 'int')] }
        self.c = fiona.open(
                os.path.join(self.tempdir, "test-no-iter.shp"),
                "w", 
                "ESRI Shapefile", 
                schema=schema,
                encoding='Windows-1252')

    def tearDown(self):
        self.c.close()
        shutil.rmtree(self.tempdir)

    def test_encoding(self):
        self.assertEquals(self.c.encoding, 'Windows-1252')

    def test_no_iter(self):
        self.assertRaises(IOError, iter, self.c)

    def test_no_filter(self):
        self.assertRaises(IOError, self.c.filter)

class PointWritingTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.sink = fiona.open(
            os.path.join(self.tempdir, "point_writing_test.shp"),
            "w",
            driver="ESRI Shapefile",
            schema={
                'geometry': 'Point', 
                'properties': [('title', 'str'), ('date', 'date')]},
            crs={'init': "epsg:4326", 'no_defs': True},
            encoding='utf-8')

    def tearDown(self):
        self.sink.close()
        shutil.rmtree(self.tempdir)

    def test_cpg(self):
        """Requires GDAL 1.9"""
        self.sink.close()
        self.failUnless(open(os.path.join(self.tempdir, "point_writing_test.cpg")).readline() == 'UTF-8')

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
        self.tempdir = tempfile.mkdtemp()
        self.sink = fiona.open(
            os.path.join(self.tempdir, "line_writing_test.shp"),
            "w",
            driver="ESRI Shapefile",
            schema={
                'geometry': 'LineString', 
                'properties': [('title', 'str'), ('date', 'date')]},
            crs={'init': "epsg:4326", 'no_defs': True})

    def tearDown(self):
        self.sink.close()
        shutil.rmtree(self.tempdir)
    
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
        self.tempdir = tempfile.mkdtemp()
        with fiona.open("docs/data/test_uk.shp", "r") as input:
            output_schema = input.schema.copy()
            output_schema['geometry'] = '3D Point'
            with fiona.open(
                    os.path.join(self.tempdir, "test_append_point.shp"),
                    "w", crs=None, driver="ESRI Shapefile", schema=output_schema
                    ) as output:
                for f in input.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
                    f['geometry'] = {
                        'type': 'Point',
                        'coordinates': f['geometry']['coordinates'][0][0] }
                    output.write(f)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_append_point(self):
        with fiona.open(os.path.join(self.tempdir, "test_append_point.shp"), "a") as c:
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
        self.tempdir = tempfile.mkdtemp()
        with fiona.open(
                os.path.join(self.tempdir, "test_append_line.shp"),
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
        shutil.rmtree(self.tempdir)

    def test_append_line(self):
        with fiona.open(os.path.join(self.tempdir, "test_append_line.shp"), "a") as c:
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
        self.tempdir = tempfile.mkdtemp()
        with fiona.open(os.path.join(self.tempdir, "textfield.shp"), "w",
                driver="ESRI Shapefile",
                schema={'geometry': 'Point', 'properties': {'text': 'str:254'}}
                ) as c:
            c.write(
                {'geometry': {'type': 'Point', 'coordinates': (0.0, 45.0)},
                 'properties': { 'text': 'a' * 254 }})
        c = fiona.open(os.path.join(self.tempdir, "textfield.shp"), "r")
        self.failUnlessEqual(c.schema['properties']['text'], 'str:254')
        f = next(iter(c))
        self.failUnlessEqual(f['properties']['text'], 'a' * 254)
        c.close()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

class CollectionTest(unittest.TestCase):

    def test_invalid_mode(self):
        self.assertRaises(ValueError, fiona.open, os.path.join(TEMPDIR, "bogus.shp"), "r+")

    def test_w_args(self):
        self.assertRaises(FionaValueError, fiona.open, os.path.join(TEMPDIR, "test-no-iter.shp"), "w")
        self.assertRaises(
            FionaValueError, fiona.open, os.path.join(TEMPDIR, "test-no-iter.shp"), "w", "Driver")

    def test_no_path(self):
        self.assertRaises(IOError, fiona.open, "no-path.shp", "a")

    def test_no_read_conn_str(self):
        self.assertRaises(IOError, fiona.open, "PG:dbname=databasename", "r")

    def test_no_read_directory(self):
        self.assertRaises(ValueError, fiona.open, "/dev/null", "r")

class GeoJSONCRSWritingTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.filename = os.path.join(self.tempdir, "crs_writing_test.json")
        self.sink = fiona.open(
            self.filename,
            "w",
            driver="GeoJSON",
            schema={
                'geometry': 'Point', 
                'properties': [('title', 'str'), ('date', 'date')]},
            crs={'a': 6370997, 'lon_0': -100, 'y_0': 0, 'no_defs': True, 'proj': 'laea', 'x_0': 0, 'units': 'm', 'b': 6370997, 'lat_0': 45})

    def tearDown(self):
        self.sink.close()
        shutil.rmtree(self.tempdir)

    def test_crs(self):
        """OGR's GeoJSON driver only deals in WGS84"""
        self.sink.close()
        info = subprocess.check_output(
            ["ogrinfo", self.filename, "OGRGeoJSON"])
        self.assert_(
            'GEOGCS["WGS 84' in info.decode('utf-8'),
            info)

