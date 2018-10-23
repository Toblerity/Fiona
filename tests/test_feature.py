"""Tests for feature objects."""

import logging
import os
import shutil
import sys
import tempfile
import pytest

import fiona
from fiona import collection
from fiona.collection import Collection
from fiona.ogrext import featureRT


class TestPointRoundTrip(object):

    def setup(self):
        self.tempdir = tempfile.mkdtemp()
        schema = {'geometry': 'Point', 'properties': {'title': 'str'}}
        self.c = Collection(os.path.join(self.tempdir, "foo.shp"),
                            "w", driver="ESRI Shapefile", schema=schema)

    def teardown(self):
        self.c.close()
        shutil.rmtree(self.tempdir)

    def test_geometry(self):
        f = { 'id': '1',
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        assert (
            sorted(g['geometry'].items()) ==
            [('coordinates', (0.0, 0.0)), ('type', 'Point')])

    def test_properties(self):
        f = { 'id': '1',
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        assert g['properties']['title'] == 'foo'

    def test_none_property(self):
        f = { 'id': '1',
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': None} }
        g = featureRT(f, self.c)
        assert g['properties']['title'] is None


class TestLineStringRoundTrip(object):

    def setup(self):
        self.tempdir = tempfile.mkdtemp()
        schema = {'geometry': 'LineString', 'properties': {'title': 'str'}}
        self.c = Collection(os.path.join(self.tempdir, "foo.shp"),
                            "w", "ESRI Shapefile", schema=schema)

    def teardown(self):
        self.c.close()
        shutil.rmtree(self.tempdir)

    def test_geometry(self):
        f = { 'id': '1',
              'geometry': { 'type': 'LineString',
                            'coordinates': [(0.0, 0.0), (1.0, 1.0)] },
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        assert (
            sorted(g['geometry'].items()) ==
            [('coordinates', [(0.0, 0.0), (1.0, 1.0)]),
             ('type', 'LineString')])

    def test_properties(self):
        f = { 'id': '1',
              'geometry': {'type': 'Point', 'coordinates': (0.0, 0.0)},
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        assert g['properties']['title'] == 'foo'


class TestPolygonRoundTrip(object):

    def setup(self):
        self.tempdir = tempfile.mkdtemp()
        schema = {'geometry': 'Polygon', 'properties': {'title': 'str'}}
        self.c = Collection(os.path.join(self.tempdir, "foo.shp"),
                            "w", "ESRI Shapefile", schema=schema)

    def teardown(self):
        self.c.close()
        shutil.rmtree(self.tempdir)

    def test_geometry(self):
        f = { 'id': '1',
              'geometry': { 'type': 'Polygon',
                            'coordinates':
                                [[(0.0, 0.0),
                                  (0.0, 1.0),
                                  (1.0, 1.0),
                                  (1.0, 0.0),
                                  (0.0, 0.0)]] },
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        assert (
            sorted(g['geometry'].items()) ==
            [('coordinates', [[(0.0, 0.0),
                                  (0.0, 1.0),
                                  (1.0, 1.0),
                                  (1.0, 0.0),
                                  (0.0, 0.0)]]),
             ('type', 'Polygon')])

    def test_properties(self):
        f = { 'id': '1',
              'geometry': { 'type': 'Polygon',
                            'coordinates':
                                [[(0.0, 0.0),
                                  (0.0, 1.0),
                                  (1.0, 1.0),
                                  (1.0, 0.0),
                                  (0.0, 0.0)]] },
              'properties': {'title': u'foo'} }
        g = featureRT(f, self.c)
        assert g['properties']['title'] == 'foo'


@pytest.mark.parametrize("driver, extension", [("ESRI Shapefile", "shp"), ("GeoJSON", "geojson")])
def test_feature_null_field(tmpdir, driver, extension):
    """
    In GDAL 2.2 the behaviour of OGR_F_IsFieldSet slightly changed. Some drivers
    (e.g. GeoJSON) also require fields to be explicitly set to null.
    See GH #460.
    """
    meta = {"driver": driver, "schema": {"geometry": "Point", "properties": {"RETURN_P": "str"}}}
    filename = os.path.join(str(tmpdir), "test_null."+extension)
    with fiona.open(filename, "w", **meta) as dst:
        g = {"coordinates": [1.0, 2.0], "type": "Point"}
        feature = {"geometry": g, "properties": {"RETURN_P": None}}
        dst.write(feature)

    with fiona.open(filename, "r") as src:
        feature = next(iter(src))
        assert(feature["properties"]["RETURN_P"] is None)
