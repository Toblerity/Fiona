
import logging
import os
import os.path
import shutil
import sys
import tempfile
import unittest

import pytest

import fiona
from fiona.collection import supported_drivers
from fiona.errors import FionaValueError, DriverError, SchemaError, CRSError
from fiona.ogrext import calc_gdal_version_num, get_gdal_version_num


logging.basicConfig(stream=sys.stderr, level=logging.INFO)


class ReadingTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

    @pytest.mark.skipif(not os.path.exists('tests/data/coutwildrnp.gpkg'),
                        reason="Requires geopackage fixture")
    def test_gpkg(self):
        if get_gdal_version_num() < calc_gdal_version_num(1, 11, 0):
            self.assertRaises(DriverError, fiona.open, 'tests/data/coutwildrnp.gpkg', 'r', driver="GPKG")
        else:
            with fiona.open('tests/data/coutwildrnp.gpkg', 'r', driver="GPKG") as c:
                self.assertEquals(len(c), 48)


class WritingTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    @pytest.mark.skipif(not os.path.exists('tests/data/coutwildrnp.gpkg'),
                        reason="Requires geopackage fixture")
    def test_gpkg(self):
        schema = {'geometry': 'Point',
                  'properties': [('title', 'str')]}
        crs = {
            'a': 6370997,
            'lon_0': -100,
            'y_0': 0,
            'no_defs': True,
            'proj': 'laea',
            'x_0': 0,
            'units': 'm',
            'b': 6370997,
            'lat_0': 45}

        path = os.path.join(self.tempdir, 'foo.gpkg')
        
        if get_gdal_version_num() < calc_gdal_version_num(1, 11, 0):
            self.assertRaises(DriverError,
                        fiona.open,
                        path,
                        'w',
                        driver='GPKG',
                        schema=schema,
                        crs=crs)
        else:
            with fiona.open(path, 'w',
                            driver='GPKG',
                            schema=schema,
                            crs=crs) as c:
                c.writerecords([{
                    'geometry': {'type': 'Point', 'coordinates': [0.0, 0.0]},
                    'properties': {'title': 'One'}}])
                c.writerecords([{
                    'geometry': {'type': 'Point', 'coordinates': [2.0, 3.0]},
                    'properties': {'title': 'Two'}}])
            with fiona.open(path) as c:
                self.assertEquals(c.schema['geometry'], 'Point')
                self.assertEquals(len(c), 2)
