# Testing BytesCollection
import unittest

import fiona

class ReadingTest(unittest.TestCase):

    def setUp(self):
        with open('tests/data/coutwildrnp.json') as src:
            strbuf = src.read()
        self.c = fiona.BytesCollection(strbuf)

    def tearDown(self):
        self.c.close()

    def test_open_repr(self):
        # I'm skipping checking the name of the virtual file as it produced by uuid.
        self.failUnless(
            repr(self.c).startswith("<open BytesCollection '/vsimem/") and
            repr(self.c).endswith(":OGRGeoJSON', mode 'r' at %s>" % hex(id(self.c))))

    def test_closed_repr(self):
        # I'm skipping checking the name of the virtual file as it produced by uuid.
        self.c.close()
        self.failUnless(
            repr(self.c).startswith("<closed BytesCollection '/vsimem/") and
            repr(self.c).endswith(":OGRGeoJSON', mode 'r' at %s>" % hex(id(self.c))))

    def test_path(self):
        self.failUnlessEqual(self.c.path, self.c.virtual_file)

    def test_closed_virtual_file(self):
        self.c.close()
        self.failUnless(self.c.virtual_file is None)

    def test_closed_buf(self):
        self.c.close()
        self.failUnless(self.c.strbuf is None)

    def test_name(self):
        self.failUnlessEqual(self.c.name, 'OGRGeoJSON')

    def test_mode(self):
        self.failUnlessEqual(self.c.mode, 'r')

    def test_collection(self):
        self.failUnlessEqual(self.c.encoding, 'utf-8')

    def test_iter(self):
        self.failUnless(iter(self.c))

    def test_closed_no_iter(self):
        self.c.close()
        self.assertRaises(ValueError, iter, self.c)

    def test_len(self):
        self.failUnlessEqual(len(self.c), 67)

    def test_closed_len(self):
        # Len is lazy, it's never computed in this case. TODO?
        self.c.close()
        self.failUnlessEqual(len(self.c), 0)

    def test_len_closed_len(self):
        # Lazy len is computed in this case and sticks.
        len(self.c)
        self.c.close()
        self.failUnlessEqual(len(self.c), 67)

    def test_driver(self):
        self.failUnlessEqual(self.c.driver, "GeoJSON")

    def test_closed_driver(self):
        self.c.close()
        self.failUnlessEqual(self.c.driver, None)

    def test_driver_closed_driver(self):
        self.c.driver
        self.c.close()
        self.failUnlessEqual(self.c.driver, "GeoJSON")

    def test_schema(self):
        s = self.c.schema['properties']
        self.failUnlessEqual(s['PERIMETER'], "float")
        self.failUnlessEqual(s['NAME'], "str")
        self.failUnlessEqual(s['URL'], "str")
        self.failUnlessEqual(s['STATE_FIPS'], "str")
        self.failUnlessEqual(s['WILDRNP020'], "int")

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
        self.failUnlessEqual(crs['init'], 'epsg:4326')

    def test_crs_wkt(self):
        crs = self.c.crs_wkt
        self.failUnless(crs.startswith('GEOGCS["WGS 84"'))

    def test_closed_crs(self):
        # Crs is lazy too, never computed in this case. TODO?
        self.c.close()
        self.failUnlessEqual(self.c.crs, None)

    def test_crs_closed_crs(self):
        self.c.crs
        self.c.close()
        self.failUnlessEqual(
            sorted(self.c.crs.keys()),
            ['init'])

    def test_meta(self):
        self.failUnlessEqual(
            sorted(self.c.meta.keys()),
            ['crs', 'driver', 'schema'])

    def test_bounds(self):
        self.failUnlessAlmostEqual(self.c.bounds[0], -113.564247, 6)
        self.failUnlessAlmostEqual(self.c.bounds[1], 37.068981, 6)
        self.failUnlessAlmostEqual(self.c.bounds[2], -104.970871, 6)
        self.failUnlessAlmostEqual(self.c.bounds[3], 41.996277, 6)

    def test_iter_one(self):
        itr = iter(self.c)
        f = next(itr)
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['STATE'], 'UT')

    def test_iter_list(self):
        f = list(self.c)[0]
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['STATE'], 'UT')

    def test_re_iter_list(self):
        f = list(self.c)[0] # Run through iterator
        f = list(self.c)[0] # Run through a new, reset iterator
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['STATE'], 'UT')

    def test_getitem_one(self):
        f = self.c[0]
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['STATE'], 'UT')

    def test_no_write(self):
        self.assertRaises(IOError, self.c.write, {})

    def test_iter_items_list(self):
        i, f = list(self.c.items())[0]
        self.failUnlessEqual(i, 0)
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['STATE'], 'UT')

    def test_iter_keys_list(self):
        i = list(self.c.keys())[0]
        self.failUnlessEqual(i, 0)

    def test_in_keys(self):
        self.failUnless(0 in self.c.keys())
        self.failUnless(0 in self.c)

class FilterReadingTest(unittest.TestCase):

    def setUp(self):
        with open('tests/data/coutwildrnp.json') as src:
            strbuf = src.read()
        self.c = fiona.BytesCollection(strbuf)

    def tearDown(self):
        self.c.close()

    def test_filter_1(self):
        results = list(self.c.filter(bbox=(-120.0, 30.0, -100.0, 50.0)))
        self.failUnlessEqual(len(results), 67)
        f = results[0]
        self.failUnlessEqual(f['id'], "0")
        self.failUnlessEqual(f['properties']['STATE'], 'UT')

    def test_filter_reset(self):
        results = list(self.c.filter(bbox=(-112.0, 38.0, -106.0, 40.0)))
        self.failUnlessEqual(len(results), 26)
        results = list(self.c.filter())
        self.failUnlessEqual(len(results), 67)

    def test_filter_mask(self):
        mask = {
            'type': 'Polygon',
            'coordinates': (
                ((-112, 38), (-112, 40), (-106, 40), (-106, 38), (-112, 38)),)}
        results = list(self.c.filter(mask=mask))
        self.failUnlessEqual(len(results), 26)



