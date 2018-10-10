
import logging
import os
import shutil
import sys
import tempfile
import unittest
import pytest

import fiona
from fiona.collection import supported_drivers
from fiona.errors import FionaValueError, DriverError, SchemaError, CRSError


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
        """Write a simple GeoJSON file"""
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
        """Overwrite an existing GeoJSON file"""
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

        # write some data to a file
        with fiona.open(path, "w", driver=driver, schema=schema1) as c:
            c.writerecords(features1)

        # test the data was written correctly
        with fiona.open(path, "r") as c:
            self.assertEqual(len(c), 2)
            feature = next(iter(c))
            self.assertEqual(feature["properties"]["title"], "One")

        # attempt to overwrite the existing file with some new data
        with fiona.open(path, "w", driver=driver, schema=schema2) as c:
            c.writerecords(features2)

        # test the second file was written correctly
        with fiona.open(path, "r") as c:
            self.assertEqual(len(c), 1)
            feature = next(iter(c))
            self.assertEqual(feature["properties"]["other"], "Three")

    def test_json_overwrite_invalid(self):
        """Overwrite an existing file that isn't a valid GeoJSON"""

        # write some invalid data to a file
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

        # attempt to overwrite it with a valid file
        with fiona.open(path, "w", driver="GeoJSON", schema=schema1) as dst:
            dst.writerecords(features1)

        # test the data was written correctly
        with fiona.open(path, "r") as src:
            self.assertEqual(len(src), 2)

    def test_write_json_invalid_directory(self):
        """Attempt to create a file in a directory that doesn't exist"""
        path = os.path.join(self.tempdir, "does-not-exist", "foo.json")
        schema = {"geometry": "Unknown", "properties": [("title", "str")]}
        with pytest.raises(DriverError):
            dst = fiona.open(path, "w", driver="GeoJSON", schema=schema)
