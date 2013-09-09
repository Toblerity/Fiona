
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
        self.c = fiona.open('docs/data/test_uk.json', 'r')
    
    def tearDown(self):
        self.c.close()

    def test_json(self):
        self.assertEquals(len(self.c), 48)

class WritingTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_json(self):
        path = os.path.join(self.tempdir, 'foo.json')
        with fiona.open(path, 'w', 
                driver='GeoJSON', 
                schema={'geometry': 'Unknown', 'properties': [('title', 'str')]}) as c:
            c.writerecords([{
                'geometry': {'type': 'Point', 'coordinates': [0.0, 0.0]},
                'properties': {'title': 'One'}}])
            c.writerecords([{
                'geometry': {'type': 'MultiPoint', 'coordinates': [[0.0, 0.0]]},
                'properties': {'title': 'Two'}}])
        with fiona.open(path) as c:
            self.assertEquals(c.schema['geometry'], 'Unknown')
            self.assertEquals(len(c), 2)
