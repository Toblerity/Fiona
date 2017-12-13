# coding=utf-8
"""Encoding tests"""

from glob import glob
import logging
import os
import shutil
import tempfile
import unittest

import pytest

import fiona


logging.basicConfig(level=logging.DEBUG)


# Uncomment when merged to master, where we're using pytest.
# We're still holding our noses in maint-1.7.
# @pytest.fixture(scope='function')
# def gre_shp_cp1252():
#     """A tempdir containing copies of gre.* files, .cpg set to cp1252
#
#     The shapefile attributes are in fact utf-8 encoded.
#     """
#     test_files = glob(os.path.join(os.path.dirname(__file__), 'data/gre.*'))
#     tmpdir = pytest.ensuretemp('tests/data')
#     for filename in test_files:
#         shutil.copy(filename, str(tmpdir))
#     tmpdir.join('gre.cpg').write('cp1252')
#     return tmpdir

class BadCodePointTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.mkdtemp(prefix='badcodepointtest')
        test_files = glob(os.path.join(os.path.dirname(__file__), 'data/gre.*'))
        for filename in test_files:
            shutil.copy(filename, self.tempdir)
        with open(os.path.join(self.tempdir, 'gre.cpg'), 'w') as cpg:
            cpg.write('cp1252')
        self.shapefile = os.path.join(self.tempdir, 'gre.shp')

    def tearDown(self):
        shutil.rmtree(self.tempdir)

    def test_broken_encoding(self):
        """Reading as cp1252 mis-encodes a Russian name"""
        with fiona.open(self.shapefile) as src:
            self.assertNotEqual(next(iter(src))['properties']['name_ru'], u'Гренада')

    def test_override_encoding(self):
        """utf-8 override succeeds"""
        with fiona.open(self.shapefile, encoding='utf-8') as src:
            self.assertEqual(next(iter(src))['properties']['name_ru'], u'Гренада')
