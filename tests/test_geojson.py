
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

        driver = "GeoJSON"
        schema1 = {"geometry": "Unknown", "properties": [("title", "str")]}
        schema2 = {"geometry": "Unknown", "properties": [("other", "str")]}

        features1 = [
            {
                "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
                "properties": {"title": "One"},
            },
            {
                "geometry": {"type": "MultiPoint", "coordinates": [[0.0, 0.0]]},
                "properties": {"title": "Two"},
            }
        ]
        features2 = [
            {
                "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
                "properties": {"other": "Three"},
            },
        ]

        with fiona.open(path, "w", driver=driver, schema=schema1) as c:
            c.writerecords(features1)
        
        with fiona.open(path, "r") as c:
            self.assertEqual(len(c), 2)
            feature = next(iter(c))
            self.assertEqual(feature["properties"]["title"], "One")

        with fiona.open(path, "w", driver=driver, schema=schema2) as c:
            c.writerecords(features2)

        with fiona.open(path, "r") as c:
            self.assertEqual(len(c), 1)
            feature = next(iter(c))
            self.assertEqual(feature["properties"]["other"], "Three")

    def test_json_overwrite_invalid(self):
        """Overwrite an existing file that isn't a valid GeoJSON"""

        path = os.path.join(self.tempdir, "foo.json")
        with open(path, "w") as f:
            f.write("This isn't a valid GeoJSON file!!!")

        schema1 = {"geometry": "Unknown", "properties": [("title", "str")]}
        features1 = [
            {
                "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
                "properties": {"title": "One"},
            },
            {
                "geometry": {"type": "MultiPoint", "coordinates": [[0.0, 0.0]]},
                "properties": {"title": "Two"},
            }
        ]

        with fiona.open(path, "w", driver="GeoJSON", schema=schema1) as dst:
            dst.writerecords(features1)

        with fiona.open(path, "r") as src:
            self.assertEqual(len(src), 2)
