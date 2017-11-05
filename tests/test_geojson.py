
import logging
import os
import shutil
import sys
import tempfile
import unittest

import fiona
from fiona.collection import supported_drivers
from fiona.errors import FionaValueError, DriverError, SchemaError, CRSError


# logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

log = logging.getLogger(__name__)


class ReadingTest(unittest.TestCase):
    
    def setUp(self):
        self.c = fiona.open('tests/data/coutwildrnp.json', 'r')
    
    def tearDown(self):
        self.c.close()

    def test_json(self):
        self.assertEqual(len(self.c), 67)

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
            self.assertEqual(c.schema['geometry'], 'Unknown')
            self.assertEqual(len(c), 2)

    def test_json_overwrite(self):
        path = os.path.join(self.tempdir, 'foo.json')

        with fiona.drivers(), fiona.open(path, 'w', 
                driver='GeoJSON', 
                schema={'geometry': 'Unknown', 'properties': [('title', 'str')]}) as c:
            c.writerecords([{
                'geometry': {'type': 'Point', 'coordinates': [0.0, 0.0]},
                'properties': {'title': 'One'}}])
            c.writerecords([{
                'geometry': {'type': 'MultiPoint', 'coordinates': [[0.0, 0.0]]},
                'properties': {'title': 'Two'}}])

        # Overwrite should raise DriverIOError.
        try:
            with fiona.drivers(), fiona.open(path, 'w', driver='GeoJSON', 
                    schema={'geometry': 'Unknown', 'properties': [('title', 'str')]}) as c:
                pass
        except IOError:
            pass
