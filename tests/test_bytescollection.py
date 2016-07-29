"""Tests for `fiona.collection.BytesCollection()`."""


import sys
import unittest

import pytest
import six

import fiona


FIXME_WINDOWS = sys.platform.startswith('win')


@pytest.fixture(scope='function')
def bytecol(path_coutwildrnp_json, request):
    """Return an open ``BytesCollection()`` which is automatically closed on
    teardown."""
    with open(path_coutwildrnp_json) as src:
        bytesbuf = src.read().encode('utf-8')
    bc = fiona.BytesCollection(bytesbuf)
    def fin():
        bc.close()
    request.addfinalizer(fin)
    return bc


@unittest.skipIf(six.PY2, 'string are bytes in Python 2')
def test_construct_with_str(path_coutwildrnp_json):
    with open(path_coutwildrnp_json) as src:
        strbuf = src.read()
    with pytest.raises(ValueError):
        fiona.BytesCollection(strbuf)


@unittest.skipIf(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Please look into why this test is not working.")
def test_open_repr(bytecol):
    """Skip checking the name of the virtual file as it produced by uuid."""
    assert repr(bytecol).startswith("<open BytesCollection '/vsimem/")
    assert repr(bytecol).endswith(":OGRGeoJSON', mode 'r' at %s>" % hex(id(bytecol)))


@unittest.skipIf(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Please look into why this test is not working.")
def test_closed_repr(bytecol):
    """Skip checking the name of the virtual file as it produced by uuid."""
    bytecol.close()
    assert repr(bytecol).startswith("<closed BytesCollection '/vsimem/")
    assert repr(bytecol).endswith(":OGRGeoJSON', mode 'r' at %s>" % hex(id(bytecol)))


def test_path(bytecol):
    assert bytecol.path == bytecol.virtual_file


def test_closed_virtual_file(bytecol):
    bytecol.close()
    assert bytecol.virtual_file is None


def test_closed_buf(bytecol):
    bytecol.close()
    assert bytecol.bytesbuf is None


def test_name(bytecol):
    assert bytecol.name == 'OGRGeoJSON'


def test_mode(bytecol):
    assert bytecol.mode == 'r'


@unittest.skipIf(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Please look into why this test is not working.")
def test_collection(bytecol):
    assert bytecol.encoding == 'utf-8'


def test_iter(bytecol):
    assert iter(bytecol)


def test_closed_no_iter(bytecol):
    bytecol.close()
    with pytest.raises(ValueError):
        iter(bytecol)


def test_len(bytecol):
    assert len(bytecol) == 67


def test_closed_len(bytecol):
    """Len is lazy, it's never computed in this case. TODO?"""
    bytecol.close()
    assert len(bytecol) == 0


def test_len_closed_len(bytecol):
    """Lazy len is computed in this case and sticks."""
    len(bytecol)
    bytecol.close()
    assert len(bytecol) == 67


def test_driver(bytecol):
    assert bytecol.driver == "GeoJSON"


def test_closed_driver(bytecol):
    bytecol.close()
    assert bytecol.driver is None


def test_driver_closed_driver(bytecol):
    bytecol.driver
    bytecol.close()
    assert bytecol.driver == "GeoJSON"


def test_schema(bytecol):
    s = bytecol.schema['properties']
    assert s['PERIMETER'] == "float"
    assert s['NAME'] == "str"
    assert s['URL'] == "str"
    assert s['STATE_FIPS'] == "str"
    assert s['WILDRNP020'] == "int"


def test_closed_schema(bytecol):
    """Schema is lazy too, never computed in this case. TODO?"""
    bytecol.close()
    assert bytecol.schema is None


def test_schema_closed_schema(bytecol):
    bytecol.schema
    bytecol.close()
    assert sorted(bytecol.schema.keys()) == ['geometry', 'properties']


def test_crs(bytecol):
    assert bytecol.crs['init'] == 'epsg:4326'


def test_crs_wkt(bytecol):
    assert bytecol.crs_wkt.startswith('GEOGCS["WGS 84"')


def test_closed_crs(bytecol):
    """CRS is lazy too, never computed in this case. TODO?"""
    bytecol.close()
    assert bytecol.crs is None


def test_crs_closed_crs(bytecol):
    bytecol.crs
    bytecol.close()
    assert sorted(bytecol.crs.keys()) == ['init']


def test_meta(bytecol):
    assert sorted(bytecol.meta.keys()) == ['crs', 'crs_wkt', 'driver', 'schema']


def test_bounds(bytecol):
    assert round(bytecol.bounds[0], 6) == round(-113.564247, 6)
    assert round(bytecol.bounds[1], 6) == round(37.068981, 6)
    assert round(bytecol.bounds[2], 6) == round(-104.970871, 6)
    assert round(bytecol.bounds[3], 6) == round(41.996277, 6)


def test_iter_one(bytecol):
    itr = iter(bytecol)
    f = next(itr)
    assert f['id'] == "0"
    assert f['properties']['STATE'] == 'UT'


def test_iter_list(bytecol):
    f = list(bytecol)[0]
    assert f['id'] == "0"
    assert f['properties']['STATE'] == 'UT'


def test_re_iter_list(bytecol):
    f = list(bytecol)[0]  # Run through iterator
    f = list(bytecol)[0]  # Run through a new, reset iterator
    assert f['id'] == "0"
    assert f['properties']['STATE'] == 'UT'


def test_getitem_one(bytecol):
    f = bytecol[0]
    assert f['id'] == "0"
    assert f['properties']['STATE'] == 'UT'


def test_no_write(bytecol):
    with pytest.raises(IOError):
        bytecol.write({})


def test_iter_items_list(bytecol):
    i, f = list(bytecol.items())[0]
    assert i == 0
    assert f['id'] == "0"
    assert f['properties']['STATE'] == 'UT'


def test_iter_keys_list(bytecol):
    i = list(bytecol.keys())[0]
    assert i == 0


def test_in_keys(bytecol):
    assert 0 in bytecol.keys()
    assert 0 in bytecol


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
