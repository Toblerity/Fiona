"""Tests for geometry objects."""

import logging
import sys
import unittest

import pytest

from fiona._geometry import (GeomBuilder, geometryRT)
from fiona.errors import UnsupportedGeometryTypeError


def geometry_wkb(wkb):
    return GeomBuilder().build_wkb(wkb)


def test_ogr_builder_exceptions():
    geom = {'type': "Bogus", 'coordinates': None}
    with pytest.raises(ValueError):
        geometryRT(geom)


@pytest.mark.parametrize('geom_type, coordinates', [
    ('Point', (0.0, 0.0)),
    ('LineString', [(0.0, 0.0), (1.0, 1.0)]),
    ('Polygon',
     [[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]]),
    ('MultiPoint', [(0.0, 0.0), (1.0, 1.0)]),
    ('MultiLineString', [[(0.0, 0.0), (1.0, 1.0)]]),
    ('MultiPolygon',
     [[[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0), (0.0, 0.0)]]]),
])
def test_round_tripping(geom_type, coordinates):
    result = geometryRT({'type': geom_type, 'coordinates': coordinates})
    assert result['type'] == geom_type
    assert result['coordinates'] == coordinates


@pytest.mark.parametrize('geom_type, coordinates', [
    ('Polygon', [[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]]),
    ('MultiPolygon', [[[(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]]]),
])
def test_implicitly_closed_round_tripping(geom_type, coordinates):
    result = geometryRT({'type': geom_type, 'coordinates': coordinates})
    assert result['type'] == geom_type
    result_coordinates = result['coordinates']
    while not isinstance(coordinates[0], tuple):
        result_coordinates = result_coordinates[0]
        coordinates = coordinates[0]
    assert result_coordinates[:-1] == coordinates


def test_geometry_collection_round_trip():
    geom = {
        'type': "GeometryCollection",
        'geometries': [
            {'type': "Point", 'coordinates': (0.0, 0.0)}, {
                'type': "LineString",
                'coordinates': [(0.0, 0.0), (1.0, 1.0)]}]}

    result = geometryRT(geom)
    assert len(result['geometries']) == 2
    assert [g['type'] for g in result['geometries']] == ['Point', 'LineString']


class PointTest(unittest.TestCase):
    def test_point(self):
        # Hex-encoded Point (0 0)
        try:
            wkb = bytes.fromhex("010100000000000000000000000000000000000000")
        except:
            wkb = "010100000000000000000000000000000000000000".decode('hex')
        geom = geometry_wkb(wkb)
        self.assertEqual(geom['type'], "Point")
        self.assertEqual(geom['coordinates'], (0.0, 0.0))

class LineStringTest(unittest.TestCase):
    def test_line(self):
        # Hex-encoded LineString (0 0, 1 1)
        try:
            wkb = bytes.fromhex("01020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f")
        except:
            wkb = "01020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.assertEqual(geom['type'], "LineString")
        self.assertEqual(geom['coordinates'], [(0.0, 0.0), (1.0, 1.0)])

class PolygonTest(unittest.TestCase):
    def test_polygon(self):
        # 1 x 1 box (0, 0, 1, 1)
        try:
            wkb = bytes.fromhex("01030000000100000005000000000000000000f03f0000000000000000000000000000f03f000000000000f03f0000000000000000000000000000f03f00000000000000000000000000000000000000000000f03f0000000000000000")
        except:
            wkb = "01030000000100000005000000000000000000f03f0000000000000000000000000000f03f000000000000f03f0000000000000000000000000000f03f00000000000000000000000000000000000000000000f03f0000000000000000".decode('hex')
        geom = geometry_wkb(wkb)
        self.assertEqual(geom['type'], "Polygon")
        self.assertEqual(len(geom['coordinates']), 1)
        self.assertEqual(len(geom['coordinates'][0]), 5)
        x, y = zip(*geom['coordinates'][0])
        self.assertEqual(min(x), 0.0)
        self.assertEqual(min(y), 0.0)
        self.assertEqual(max(x), 1.0)
        self.assertEqual(max(y), 1.0)

class MultiPointTest(unittest.TestCase):
    def test_multipoint(self):
        try:
            wkb = bytes.fromhex("0104000000020000000101000000000000000000000000000000000000000101000000000000000000f03f000000000000f03f")
        except:
            wkb = "0104000000020000000101000000000000000000000000000000000000000101000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.assertEqual(geom['type'], "MultiPoint")
        self.assertEqual(geom['coordinates'], [(0.0, 0.0), (1.0, 1.0)])

class MultiLineStringTest(unittest.TestCase):
    def test_multilinestring(self):
        # Hex-encoded LineString (0 0, 1 1)
        try:
            wkb = bytes.fromhex("01050000000100000001020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f")
        except:
            wkb = "01050000000100000001020000000200000000000000000000000000000000000000000000000000f03f000000000000f03f".decode('hex')
        geom = geometry_wkb(wkb)
        self.assertEqual(geom['type'], "MultiLineString")
        self.assertEqual(len(geom['coordinates']), 1)
        self.assertEqual(len(geom['coordinates'][0]), 2)
        self.assertEqual(geom['coordinates'][0], [(0.0, 0.0), (1.0, 1.0)])

class MultiPolygonTest(unittest.TestCase):
    def test_multipolygon(self):
        # [1 x 1 box (0, 0, 1, 1)]
        try:
            wkb = bytes.fromhex("01060000000100000001030000000100000005000000000000000000f03f0000000000000000000000000000f03f000000000000f03f0000000000000000000000000000f03f00000000000000000000000000000000000000000000f03f0000000000000000")
        except:
            wkb = "01060000000100000001030000000100000005000000000000000000f03f0000000000000000000000000000f03f000000000000f03f0000000000000000000000000000f03f00000000000000000000000000000000000000000000f03f0000000000000000".decode('hex')
        geom = geometry_wkb(wkb)
        self.assertEqual(geom['type'], "MultiPolygon")
        self.assertEqual(len(geom['coordinates']), 1)
        self.assertEqual(len(geom['coordinates'][0]), 1)
        self.assertEqual(len(geom['coordinates'][0][0]), 5)
        x, y = zip(*geom['coordinates'][0][0])
        self.assertEqual(min(x), 0.0)
        self.assertEqual(min(y), 0.0)
        self.assertEqual(max(x), 1.0)
        self.assertEqual(max(y), 1.0)
