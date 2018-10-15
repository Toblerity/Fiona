# Testing collections and workspaces

import datetime
import logging
import os
import shutil
import sys
import tempfile
import unittest
import re

import pytest

import fiona
from fiona.collection import Collection, supported_drivers
from fiona.errors import FionaValueError, DriverError

from .conftest import WGS84PATTERN


TEMPDIR = tempfile.gettempdir()


class SupportedDriversTest(unittest.TestCase):

    def test_shapefile(self):
        self.assertTrue("ESRI Shapefile" in supported_drivers)
        self.assertEqual(
            set(supported_drivers["ESRI Shapefile"]), set("raw"))

    def test_map(self):
        self.assertTrue("MapInfo File" in supported_drivers)
        self.assertEqual(
            set(supported_drivers["MapInfo File"]), set("raw"))


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
        self.assertRaises(DriverError, fiona.open, ("/"), mode='r', vfs="zip:///foo.zip")


@pytest.mark.usefixtures("unittest_path_coutwildrnp_shp")
class ReadingTest(unittest.TestCase):

    def setUp(self):
        self.c = fiona.open(self.path_coutwildrnp_shp, "r")

    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        self.assertEqual(
            repr(self.c),
            ("<open Collection '{path}:coutwildrnp', mode 'r' "
             "at {hexid}>".format(hexid=hex(id(self.c)), path=self.path_coutwildrnp_shp)))

    def test_closed_repr(self):
        self.c.close()
        self.assertEqual(
            repr(self.c),
            ("<closed Collection '{path}:coutwildrnp', mode 'r' "
             "at {hexid}>".format(hexid=hex(id(self.c)), path=self.path_coutwildrnp_shp)))

    def test_path(self):
        self.assertEqual(self.c.path, self.path_coutwildrnp_shp)

    def test_name(self):
        self.assertEqual(self.c.name, 'coutwildrnp')

    def test_mode(self):
        self.assertEqual(self.c.mode, 'r')

    def test_collection(self):
        self.assertEqual(self.c.encoding, 'iso-8859-1')

    def test_iter(self):
        self.assertTrue(iter(self.c))

    def test_closed_no_iter(self):
        self.c.close()
        self.assertRaises(ValueError, iter, self.c)

    def test_len(self):
        self.assertEqual(len(self.c), 67)

    def test_closed_len(self):
        # Len is lazy, it's never computed in this case. TODO?
        self.c.close()
        self.assertEqual(len(self.c), 0)

    def test_len_closed_len(self):
        # Lazy len is computed in this case and sticks.
        len(self.c)
        self.c.close()
        self.assertEqual(len(self.c), 67)

    def test_driver(self):
        self.assertEqual(self.c.driver, "ESRI Shapefile")

    def test_closed_driver(self):
        self.c.close()
        self.assertEqual(self.c.driver, None)

    def test_driver_closed_driver(self):
        self.c.driver
        self.c.close()
        self.assertEqual(self.c.driver, "ESRI Shapefile")

    def test_schema(self):
        s = self.c.schema['properties']
        self.assertEqual(s['PERIMETER'], "float:24.15")
        self.assertEqual(s['NAME'], "str:80")
        self.assertEqual(s['URL'], "str:101")
        self.assertEqual(s['STATE_FIPS'], "str:80")
        self.assertEqual(s['WILDRNP020'], "int:10")

    def test_closed_schema(self):
        # Schema is lazy too, never computed in this case. TODO?
        self.c.close()
        self.assertEqual(self.c.schema, None)

    def test_schema_closed_schema(self):
        self.c.schema
        self.c.close()
        self.assertEqual(
            sorted(self.c.schema.keys()),
            ['geometry', 'properties'])

    def test_crs(self):
        crs = self.c.crs
        self.assertEqual(crs['init'], 'epsg:4326')

    def test_crs_wkt(self):
        crs = self.c.crs_wkt
        assert re.match(WGS84PATTERN, crs)

    def test_closed_crs(self):
        # Crs is lazy too, never computed in this case. TODO?
        self.c.close()
        self.assertEqual(self.c.crs, None)

    def test_crs_closed_crs(self):
        self.c.crs
        self.c.close()
        self.assertEqual(
            sorted(self.c.crs.keys()),
            ['init'])

    def test_meta(self):
        self.assertEqual(
            sorted(self.c.meta.keys()),
            ['crs', 'crs_wkt', 'driver', 'schema'])

    def test_profile(self):
        self.assertEqual(
            sorted(self.c.profile.keys()),
            ['crs', 'crs_wkt', 'driver', 'schema'])

    def test_bounds(self):
        self.assertAlmostEqual(self.c.bounds[0], -113.564247, 6)
        self.assertAlmostEqual(self.c.bounds[1], 37.068981, 6)
        self.assertAlmostEqual(self.c.bounds[2], -104.970871, 6)
        self.assertAlmostEqual(self.c.bounds[3], 41.996277, 6)

    def test_context(self):
        with fiona.open(self.path_coutwildrnp_shp, "r") as c:
            self.assertEqual(c.name, 'coutwildrnp')
            self.assertEqual(len(c), 67)
        self.assertEqual(c.closed, True)

    def test_iter_one(self):
        itr = iter(self.c)
        f = next(itr)
        self.assertEqual(f['id'], "0")
        self.assertEqual(f['properties']['STATE'], 'UT')

    def test_iter_list(self):
        f = list(self.c)[0]
        self.assertEqual(f['id'], "0")
        self.assertEqual(f['properties']['STATE'], 'UT')

    def test_re_iter_list(self):
        f = list(self.c)[0]  # Run through iterator
        f = list(self.c)[0]  # Run through a new, reset iterator
        self.assertEqual(f['id'], "0")
        self.assertEqual(f['properties']['STATE'], 'UT')

    def test_getitem_one(self):
        f = self.c[0]
        self.assertEqual(f['id'], "0")
        self.assertEqual(f['properties']['STATE'], 'UT')

    def test_getitem_iter_combo(self):
        i = iter(self.c)
        f = next(i)
        f = next(i)
        self.assertEqual(f['id'], "1")
        f = self.c[0]
        self.assertEqual(f['id'], "0")
        f = next(i)
        self.assertEqual(f['id'], "2")

    def test_no_write(self):
        self.assertRaises(IOError, self.c.write, {})

    def test_iter_items_list(self):
        i, f = list(self.c.items())[0]
        self.assertEqual(i, 0)
        self.assertEqual(f['id'], "0")
        self.assertEqual(f['properties']['STATE'], 'UT')

    def test_iter_keys_list(self):
        i = list(self.c.keys())[0]
        self.assertEqual(i, 0)

    def test_in_keys(self):
        self.assertTrue(0 in self.c.keys())
        self.assertTrue(0 in self.c)


@pytest.mark.usefixtures("unittest_path_coutwildrnp_shp")
class ReadingPathTest(unittest.TestCase):
    def test_open_path(self):
        pathlib = pytest.importorskip("pathlib")
        with fiona.open(pathlib.Path(self.path_coutwildrnp_shp)) as collection:
            assert collection.name == 'coutwildrnp'


@pytest.mark.usefixtures("unittest_path_coutwildrnp_shp")
class IgnoreFieldsAndGeometryTest(unittest.TestCase):

    def test_without_ignore(self):
        with fiona.open(self.path_coutwildrnp_shp, "r") as collection:
            assert("AREA" in collection.schema["properties"].keys())
            assert("STATE" in collection.schema["properties"].keys())
            assert("NAME" in collection.schema["properties"].keys())
            assert("geometry" in collection.schema.keys())

            feature = next(iter(collection))
            assert(feature["properties"]["AREA"] is not None)
            assert(feature["properties"]["STATE"] is not None)
            assert(feature["properties"]["NAME"] is not None)
            assert(feature["geometry"] is not None)

    def test_ignore_fields(self):
        with fiona.open(self.path_coutwildrnp_shp, "r", ignore_fields=["AREA", "STATE"]) as collection:
            assert("AREA" not in collection.schema["properties"].keys())
            assert("STATE" not in collection.schema["properties"].keys())
            assert("NAME" in collection.schema["properties"].keys())
            assert("geometry" in collection.schema.keys())

            feature = next(iter(collection))
            assert("AREA" not in feature["properties"].keys())
            assert("STATE" not in feature["properties"].keys())
            assert(feature["properties"]["NAME"] is not None)
            assert(feature["geometry"] is not None)

    def test_ignore_invalid_field_missing(self):
        with fiona.open(self.path_coutwildrnp_shp, "r", ignore_fields=["DOES_NOT_EXIST"]):
            pass

    def test_ignore_invalid_field_not_string(self):
        with self.assertRaises(TypeError):
            with fiona.open(self.path_coutwildrnp_shp, "r", ignore_fields=[42]):
                pass

    def test_ignore_geometry(self):
        with fiona.open(self.path_coutwildrnp_shp, "r", ignore_geometry=True) as collection:
            assert("AREA" in collection.schema["properties"].keys())
            assert("STATE" in collection.schema["properties"].keys())
            assert("NAME" in collection.schema["properties"].keys())
            assert("geometry" not in collection.schema.keys())

            feature = next(iter(collection))
            assert(feature["properties"]["AREA"] is not None)
            assert(feature["properties"]["STATE"] is not None)
            assert(feature["properties"]["NAME"] is not None)
            assert("geometry" not in feature.keys())


@pytest.mark.usefixtures("unittest_path_coutwildrnp_shp")
class FilterReadingTest(unittest.TestCase):

    def setUp(self):
        self.c = fiona.open(self.path_coutwildrnp_shp, "r")

    def tearDown(self):
        self.c.close()

    def test_filter_1(self):
        results = list(self.c.filter(bbox=(-120.0, 30.0, -100.0, 50.0)))
        self.assertEqual(len(results), 67)
        f = results[0]
        self.assertEqual(f['id'], "0")
        self.assertEqual(f['properties']['STATE'], 'UT')

    def test_filter_reset(self):
        results = list(self.c.filter(bbox=(-112.0, 38.0, -106.0, 40.0)))
        self.assertEqual(len(results), 26)
        results = list(self.c.filter())
        self.assertEqual(len(results), 67)

    def test_filter_mask(self):
        mask = {
            'type': 'Polygon',
            'coordinates': (
                ((-112, 38), (-112, 40), (-106, 40), (-106, 38), (-112, 38)),)}
        results = list(self.c.filter(mask=mask))
        self.assertEqual(len(results), 26)


class UnsupportedDriverTest(unittest.TestCase):

    def test_immediate_fail_driver(self):
        schema = {
            'geometry': 'Point',
            'properties': {'label': 'str', u'verit\xe9': 'int'}}
        self.assertRaises(
            DriverError,
            fiona.open, os.path.join(TEMPDIR, "foo"), "w", "Bogus", schema=schema)


class GenericWritingTest(unittest.TestCase):
    tempdir = None
    c = None

    @classmethod
    def setUpClass(self):
        self.tempdir = tempfile.mkdtemp()
        schema = {
            'geometry': 'Point',
            'properties': [('label', 'str'), (u'verit\xe9', 'int')]}
        self.c = fiona.open(os.path.join(self.tempdir, "test-no-iter.shp"),
                            'w', driver="ESRI Shapefile", schema=schema,
                            encoding='Windows-1252')

    @classmethod
    def tearDownClass(self):
        self.c.close()
        shutil.rmtree(self.tempdir)

    def test_encoding(self):
        self.assertEqual(self.c.encoding, 'Windows-1252')

    def test_no_iter(self):
        self.assertRaises(IOError, iter, self.c)

    def test_no_filter(self):
        self.assertRaises(IOError, self.c.filter)


class PropertiesNumberFormattingTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.filename = os.path.join(self.tempdir, "properties_number_formatting_test")

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    _records_with_float_property1 = [
        {
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': {'property1': 12.22}
        },
        {
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.2)},
            'properties': {'property1': 12.88}
        }
    ]

    _records_with_float_property1_as_string = [
        {
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': {'property1': '12.22'}
        },
        {
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.2)},
            'properties': {'property1': '12.88'}
        }
    ]

    _records_with_invalid_number_property1 = [
        {
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.3)},
            'properties': {'property1': 'invalid number'}
        }
    ]

    def _write_collection(self, records, schema, driver):
        with fiona.open(
                self.filename,
                "w",
                driver=driver,
                schema=schema,
                crs='epsg:4326',
                encoding='utf-8'
        ) as c:
            c.writerecords(records)

    def test_shape_driver_truncates_float_property_to_requested_int_format(self):
        driver = "ESRI Shapefile"
        self._write_collection(
            self._records_with_float_property1,
            {'geometry': 'Point', 'properties': [('property1', 'int')]},
            driver
        )

        with fiona.open(self.filename, driver=driver, encoding='utf-8') as c:
            self.assertEqual(2, len(c))

            rf1, rf2 = list(c)

            self.assertEqual(12, rf1['properties']['property1'])
            self.assertEqual(12, rf2['properties']['property1'])

    def test_shape_driver_rounds_float_property_to_requested_digits_number(self):
        driver = "ESRI Shapefile"
        self._write_collection(
            self._records_with_float_property1,
            {'geometry': 'Point', 'properties': [('property1', 'float:15.1')]},
            driver
        )

        with fiona.open(self.filename, driver=driver, encoding='utf-8') as c:
            self.assertEqual(2, len(c))

            rf1, rf2 = list(c)

            self.assertEqual(12.2, rf1['properties']['property1'])
            self.assertEqual(12.9, rf2['properties']['property1'])

    def test_string_is_converted_to_number_and_truncated_to_requested_int_by_shape_driver(self):
        driver = "ESRI Shapefile"
        self._write_collection(
            self._records_with_float_property1_as_string,
            {'geometry': 'Point', 'properties': [('property1', 'int')]},
            driver
        )

        with fiona.open(self.filename, driver=driver, encoding='utf-8') as c:
            self.assertEqual(2, len(c))

            rf1, rf2 = list(c)

            self.assertEqual(12, rf1['properties']['property1'])
            self.assertEqual(12, rf2['properties']['property1'])

    def test_string_is_converted_to_number_and_rounded_to_requested_digits_number_by_shape_driver(self):
        driver = "ESRI Shapefile"
        self._write_collection(
            self._records_with_float_property1_as_string,
            {'geometry': 'Point', 'properties': [('property1', 'float:15.1')]},
            driver
        )

        with fiona.open(self.filename, driver=driver, encoding='utf-8') as c:
            self.assertEqual(2, len(c))

            rf1, rf2 = list(c)

            self.assertEqual(12.2, rf1['properties']['property1'])
            self.assertEqual(12.9, rf2['properties']['property1'])

    def test_invalid_number_is_converted_to_0_and_written_by_shape_driver(self):
        driver = "ESRI Shapefile"
        self._write_collection(
            self._records_with_invalid_number_property1,
            # {'geometry': 'Point', 'properties': [('property1', 'int')]},
            {'geometry': 'Point', 'properties': [('property1', 'float:15.1')]},
            driver
        )

        with fiona.open(self.filename, driver=driver, encoding='utf-8') as c:
            self.assertEqual(1, len(c))

            rf1 = c[0]

            self.assertEqual(0, rf1['properties']['property1'])

    def test_geojson_driver_truncates_float_property_to_requested_int_format(self):
        driver = "GeoJSON"
        self._write_collection(
            self._records_with_float_property1,
            {'geometry': 'Point', 'properties': [('property1', 'int')]},
            driver
        )

        with fiona.open(self.filename, driver=driver, encoding='utf-8') as c:
            self.assertEqual(2, len(c))

            rf1, rf2 = list(c)

            self.assertEqual(12, rf1['properties']['property1'])
            self.assertEqual(12, rf2['properties']['property1'])

    def test_geojson_driver_does_not_round_float_property_to_requested_digits_number(self):
        driver = "GeoJSON"
        self._write_collection(
            self._records_with_float_property1,
            {'geometry': 'Point', 'properties': [('property1', 'float:15.1')]},
            driver
        )

        with fiona.open(self.filename, driver=driver, encoding='utf-8') as c:
            self.assertEqual(2, len(c))

            rf1, rf2 = list(c)

            # ****************************************
            # FLOAT FORMATTING IS NOT RESPECTED...
            self.assertEqual(12.22, rf1['properties']['property1'])
            self.assertEqual(12.88, rf2['properties']['property1'])

    def test_string_is_converted_to_number_and_truncated_to_requested_int_by_geojson_driver(self):
        driver = "GeoJSON"
        self._write_collection(
            self._records_with_float_property1_as_string,
            {'geometry': 'Point', 'properties': [('property1', 'int')]},
            driver
        )

        with fiona.open(self.filename, driver=driver, encoding='utf-8') as c:
            self.assertEqual(2, len(c))

            rf1, rf2 = list(c)

            self.assertEqual(12, rf1['properties']['property1'])
            self.assertEqual(12, rf2['properties']['property1'])

    def test_string_is_converted_to_number_but_not_rounded_to_requested_digits_number_by_geojson_driver(self):
        driver = "GeoJSON"
        self._write_collection(
            self._records_with_float_property1_as_string,
            {'geometry': 'Point', 'properties': [('property1', 'float:15.1')]},
            driver
        )

        with fiona.open(self.filename, driver=driver, encoding='utf-8') as c:
            self.assertEqual(2, len(c))

            rf1, rf2 = list(c)

            # ****************************************
            # FLOAT FORMATTING IS NOT RESPECTED...
            self.assertEqual(12.22, rf1['properties']['property1'])
            self.assertEqual(12.88, rf2['properties']['property1'])

    def test_invalid_number_is_converted_to_0_and_written_by_geojson_driver(self):
        driver = "GeoJSON"
        self._write_collection(
            self._records_with_invalid_number_property1,
            # {'geometry': 'Point', 'properties': [('property1', 'int')]},
            {'geometry': 'Point', 'properties': [('property1', 'float:15.1')]},
            driver
        )

        with fiona.open(self.filename, driver=driver, encoding='utf-8') as c:
            self.assertEqual(1, len(c))

            rf1 = c[0]

            self.assertEqual(0, rf1['properties']['property1'])


class PointWritingTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        self.filename = os.path.join(self.tempdir, "point_writing_test.shp")
        self.sink = fiona.open(
            self.filename,
            "w",
            driver="ESRI Shapefile",
            schema={
                'geometry': 'Point',
                'properties': [('title', 'str'), ('date', 'date')]},
            crs='epsg:4326',
            encoding='utf-8')

    def tearDown(self):
        self.sink.close()
        shutil.rmtree(self.tempdir)

    def test_cpg(self):
        """Requires GDAL 1.9"""
        self.sink.close()
        with open(os.path.join(self.tempdir, "point_writing_test.cpg")) as f:
            encoding = f.readline()
        self.assertTrue(encoding == "UTF-8")

    def test_write_one(self):
        self.assertEqual(len(self.sink), 0)
        self.assertEqual(self.sink.bounds, (0.0, 0.0, 0.0, 0.0))
        f = {
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': {'title': 'point one', 'date': "2012-01-29"}}
        self.sink.writerecords([f])
        self.assertEqual(len(self.sink), 1)
        self.assertEqual(self.sink.bounds, (0.0, 0.1, 0.0, 0.1))
        self.sink.close()

    def test_write_two(self):
        self.assertEqual(len(self.sink), 0)
        self.assertEqual(self.sink.bounds, (0.0, 0.0, 0.0, 0.0))
        f1 = {
            'geometry': {'type': 'Point', 'coordinates': (0.0, 0.1)},
            'properties': {'title': 'point one', 'date': "2012-01-29"}}
        f2 = {
            'geometry': {'type': 'Point', 'coordinates': (0.0, -0.1)},
            'properties': {'title': 'point two', 'date': "2012-01-29"}}
        self.sink.writerecords([f1, f2])
        self.assertEqual(len(self.sink), 2)
        self.assertEqual(self.sink.bounds, (0.0, -0.1, 0.0, 0.1))

    def test_write_one_null_geom(self):
        self.assertEqual(len(self.sink), 0)
        self.assertEqual(self.sink.bounds, (0.0, 0.0, 0.0, 0.0))
        f = {
            'geometry': None,
            'properties': {'title': 'point one', 'date': "2012-01-29"}}
        self.sink.writerecords([f])
        self.assertEqual(len(self.sink), 1)
        self.assertEqual(self.sink.bounds, (0.0, 0.0, 0.0, 0.0))

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
        self.assertEqual(len(self.sink), 0)
        self.assertEqual(self.sink.bounds, (0.0, 0.0, 0.0, 0.0))
        f = {
            'geometry': {'type': 'LineString',
                         'coordinates': [(0.0, 0.1), (0.0, 0.2)]},
            'properties': {'title': 'line one', 'date': "2012-01-29"}}
        self.sink.writerecords([f])
        self.assertEqual(len(self.sink), 1)
        self.assertEqual(self.sink.bounds, (0.0, 0.1, 0.0, 0.2))

    def test_write_two(self):
        self.assertEqual(len(self.sink), 0)
        self.assertEqual(self.sink.bounds, (0.0, 0.0, 0.0, 0.0))
        f1 = {
            'geometry': {'type': 'LineString',
                         'coordinates': [(0.0, 0.1), (0.0, 0.2)]},
            'properties': {'title': 'line one', 'date': "2012-01-29"}}
        f2 = {
            'geometry': {'type': 'MultiLineString',
                         'coordinates': [[(0.0, 0.0), (0.0, -0.1)],
                                         [(0.0, -0.1), (0.0, -0.2)]]},
            'properties': {'title': 'line two', 'date': "2012-01-29"}}
        self.sink.writerecords([f1, f2])
        self.assertEqual(len(self.sink), 2)
        self.assertEqual(self.sink.bounds, (0.0, -0.2, 0.0, 0.2))


@pytest.mark.usefixtures("unittest_path_coutwildrnp_shp")
class PointAppendTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()
        with fiona.open(self.path_coutwildrnp_shp, "r") as input:
            output_schema = input.schema.copy()
            output_schema['geometry'] = '3D Point'
            with fiona.open(
                    os.path.join(self.tempdir, "test_append_point.shp"),
                    'w', crs=None, driver="ESRI Shapefile",
                    schema=output_schema) as output:
                for f in input:
                    f['geometry'] = {
                        'type': 'Point',
                        'coordinates': f['geometry']['coordinates'][0][0]}
                    output.write(f)

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_append_point(self):
        with fiona.open(os.path.join(self.tempdir, "test_append_point.shp"), "a") as c:
            self.assertEqual(c.schema['geometry'], '3D Point')
            c.write({'geometry': {'type': 'Point', 'coordinates': (0.0, 45.0)},
                     'properties': {'PERIMETER': 1.0,
                                    'FEATURE2': None,
                                    'NAME': 'Foo',
                                    'FEATURE1': None,
                                    'URL': 'http://example.com',
                                    'AGBUR': 'BAR',
                                    'AREA': 0.0,
                                    'STATE_FIPS': 1,
                                    'WILDRNP020': 1,
                                    'STATE': 'XL'}})
            self.assertEqual(len(c), 68)


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
                             'coordinates': [[(0.0, 0.0), (0.0, -0.1)],
                                             [(0.0, -0.1), (0.0, -0.2)]]},
                'properties': {'title': 'line two', 'date': "2012-01-29"}}
            c.writerecords([f1, f2])
            self.assertEqual(len(c), 3)
            self.assertEqual(c.bounds, (0.0, -0.2, 0.0, 0.2))


class ShapefileFieldWidthTest(unittest.TestCase):

    def test_text(self):
        self.tempdir = tempfile.mkdtemp()
        with fiona.open(
                os.path.join(self.tempdir, "textfield.shp"), 'w',
                schema={'geometry': 'Point', 'properties': {'text': 'str:254'}},
                driver="ESRI Shapefile") as c:
            c.write(
                {'geometry': {'type': 'Point', 'coordinates': (0.0, 45.0)},
                 'properties': {'text': 'a' * 254}})
        c = fiona.open(os.path.join(self.tempdir, "textfield.shp"), "r")
        self.assertEqual(c.schema['properties']['text'], 'str:254')
        f = next(iter(c))
        self.assertEqual(f['properties']['text'], 'a' * 254)
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
        self.assertRaises(Exception, fiona.open, "no-path.shp", "a")

    def test_no_read_conn_str(self):
        self.assertRaises(DriverError, fiona.open, "PG:dbname=databasename", "r")

    @pytest.mark.skipif(sys.platform.startswith("win"),
                     reason="test only for *nix based system")
    def test_no_read_directory(self):
        self.assertRaises(DriverError, fiona.open, "/dev/null", "r")


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


class DateTimeTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def test_date(self):
        self.sink = fiona.open(
            os.path.join(self.tempdir, "date_test.shp"),
            "w",
            driver="ESRI Shapefile",
            schema={
                'geometry': 'Point',
                'properties': [('id', 'int'), ('date', 'date')]},
            crs={'init': "epsg:4326", 'no_defs': True})

        recs = [{
            'geometry': {'type': 'Point',
                         'coordinates': (7.0, 50.0)},
            'properties': {'id': 1, 'date': '2013-02-25'}
        }, {
            'geometry': {'type': 'Point',
                         'coordinates': (7.0, 50.2)},
            'properties': {'id': 1, 'date': datetime.date(2014, 2, 3)}
        }]
        self.sink.writerecords(recs)
        self.sink.close()
        self.assertEqual(len(self.sink), 2)

        with fiona.open(os.path.join(self.tempdir, "date_test.shp"), "r") as c:
            self.assertEqual(len(c), 2)

            rf1, rf2 = list(c)
            self.assertEqual(rf1['properties']['date'], '2013-02-25')
            self.assertEqual(rf2['properties']['date'], '2014-02-03')

    def tearDown(self):
        shutil.rmtree(self.tempdir)


class OpenKeywordArgsTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def test_kwargs(self):
        dstfile = os.path.join(self.tempdir, 'test.json')
        with fiona.open(os.path.join('tests', 'data', 'coutwildrnp.shp')) as src:
            kwds = src.profile
            kwds['driver'] = 'GeoJSON'
            kwds['coordinate_precision'] = 2
            with fiona.open(dstfile, 'w', **kwds) as dst:
                dst.writerecords(ftr for ftr in src)

        with open(dstfile) as f:
            assert '"coordinates": [ [ [ -111.74, 42.0 ], [ -111.66, 42.0 ]' in f.read(2000)

    def tearDown(self):
        shutil.rmtree(self.tempdir)


@pytest.mark.network
def test_collection_http():
    ds = fiona.Collection('http://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/poly.shp', vsi='http')
    assert ds.path == '/vsicurl/http://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/poly.shp'
    assert len(ds) == 10


@pytest.mark.network
def test_collection_zip_http():
    ds = fiona.Collection('http://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/poly.zip', vsi='zip+http')
    assert ds.path == '/vsizip/vsicurl/http://raw.githubusercontent.com/OSGeo/gdal/master/autotest/ogr/data/poly.zip'
    assert len(ds) == 10
