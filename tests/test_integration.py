"""Unittests to verify Fiona is functioning properly with other software."""


import collections
import os
import shutil
import tempfile
import unittest

import six

import fiona


class TestCRSNonDict(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.tempdir = tempfile.mkdtemp()

    @classmethod
    def tearDownClass(self):
        shutil.rmtree(self.tempdir)

    def test_dict_subclass(self):
        """Rasterio now has a `CRS()` class that subclasses
        `collections.UserDict()`.  Make sure we can receive it.

        `UserDict()` is a good class to test against because in Python 2 it is
        not a subclass of `collections.Mapping()`, so it provides an edge case.
        """

        class CRS(six.moves.UserDict):
            pass

        outfile = os.path.join(self.tempdir, 'test_UserDict.geojson')

        profile = {
            'crs': CRS(init='EPSG:4326'),
            'driver': 'GeoJSON',
            'schema': {
                'geometry': 'Point',
                'properties': {}
            }
        }

        with fiona.open(outfile, 'w', **profile) as dst:
            dst.write({
                'type': 'Feature',
                'properties': {},
                'geometry': {
                    'type': 'Point',
                    'coordinates': (10, -10)
                }
            })

        with fiona.open(outfile) as src:
            assert len(src) == 1
            assert src.crs == {'init': 'epsg:4326'}
