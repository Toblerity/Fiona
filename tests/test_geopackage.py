
import logging
import os
import shutil
import sys
import tempfile
import unittest

import fiona
from fiona.collection import supported_drivers
from fiona.errors import FionaValueError, DriverError, SchemaError, CRSError

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


class ReadingTest(unittest.TestCase):

    def setUp(self):
        self.c = fiona.open('docs/data/test_uk.gpkg', 'r')

    def tearDown(self):
        self.c.close()

    def test_json(self):
        self.assertEquals(len(self.c), 48)


class WritingTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

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

