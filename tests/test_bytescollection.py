# Testing BytesCollection
import sys
import unittest

import pytest
import six

import fiona

FIXME_WINDOWS = sys.platform.startswith('win')


class ReadingTest(unittest.TestCase):

    def setUp(self):
        with open('tests/data/coutwildrnp.json') as src:
            bytesbuf = src.read().encode('utf-8')
        self.c = fiona.BytesCollection(bytesbuf)

    def tearDown(self):
        self.c.close()

    @unittest.skipIf(six.PY2, 'string are bytes in Python 2')
    def test_construct_with_str(self):
        with open('tests/data/coutwildrnp.json') as src:
            strbuf = src.read()
        self.assertRaises(ValueError, fiona.BytesCollection, strbuf)

    @unittest.skipIf(FIXME_WINDOWS,
                     reason="FIXME on Windows. Please look into why this test is not working.")
    def test_open_repr(self):
        # I'm skipping checking the name of the virtual file as it produced by uuid.
        self.assertTrue(repr(self.c).startswith("<open BytesCollection '/vsimem/"))

    @unittest.skipIf(FIXME_WINDOWS,
                     reason="FIXME on Windows. Please look into why this test is not working.")
    def test_closed_repr(self):
        # I'm skipping checking the name of the virtual file as it produced by uuid.
        self.c.close()
        self.assertTrue(repr(self.c).startswith("<closed BytesCollection '/vsimem/"))

    def test_path(self):
        self.assertEqual(self.c.path, self.c.virtual_file)

    def test_closed_virtual_file(self):
        self.c.close()
        self.assertTrue(self.c.virtual_file is None)

    def test_closed_buf(self):
        self.c.close()
        self.assertTrue(self.c.bytesbuf is None)

    def test_name(self):
        self.assertTrue(len(self.c.name) > 0)

    def test_mode(self):
        self.assertEqual(self.c.mode, 'r')

    @unittest.skipIf(FIXME_WINDOWS,
                     reason="FIXME on Windows. Please look into why this test is not working.")
    def test_collection(self):
        self.assertEqual(self.c.encoding, 'utf-8')

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
        self.assertEqual(self.c.driver, "GeoJSON")

    def test_closed_driver(self):
        self.c.close()
        self.assertEqual(self.c.driver, None)

    def test_driver_closed_driver(self):
        self.c.driver
        self.c.close()
        self.assertEqual(self.c.driver, "GeoJSON")

    def test_schema(self):
        s = self.c.schema['properties']
        self.assertEqual(s['PERIMETER'], "float")
        self.assertEqual(s['NAME'], "str")
        self.assertEqual(s['URL'], "str")
        self.assertEqual(s['STATE_FIPS'], "str")
        self.assertEqual(s['WILDRNP020'], "int")

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
        self.assertTrue(crs.startswith('GEOGCS["WGS 84"'))

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

    def test_bounds(self):
        self.assertAlmostEqual(self.c.bounds[0], -113.564247, 6)
        self.assertAlmostEqual(self.c.bounds[1], 37.068981, 6)
        self.assertAlmostEqual(self.c.bounds[2], -104.970871, 6)
        self.assertAlmostEqual(self.c.bounds[3], 41.996277, 6)

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

class FilterReadingTest(unittest.TestCase):

    def setUp(self):
        with open('tests/data/coutwildrnp.json') as src:
            bytesbuf = src.read().encode('utf-8')
        self.c = fiona.BytesCollection(bytesbuf)

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


def test_zipped_bytes_collection():
    with open('tests/data/coutwildrnp.zip', 'rb') as src:
        zip_file_bytes = src.read()

    with fiona.BytesCollection(zip_file_bytes) as col:
        assert col.name == 'coutwildrnp'


def test_grenada_bytes_geojson():
    """Read grenada.geojson as BytesCollection.

    grenada.geojson is an example of geojson that GDAL's GeoJSON
    driver will fail to read successfully unless the file's extension
    reflects its json'ness.
    """
    with open('tests/data/grenada.geojson', 'rb') as src:
        bytes_grenada_geojson = src.read()
    
    # We expect an exception if the GeoJSON driver isn't specified.
    with pytest.raises(fiona.errors.FionaValueError):
        with fiona.BytesCollection(bytes_grenada_geojson) as col:
            pass

    # If told what driver to use, we should be good.
    with fiona.BytesCollection(bytes_grenada_geojson, driver='GeoJSON') as col:        
        assert len(col) == 1
        
