# coding=utf-8
"""Encoding tests"""

from glob import glob
import logging
import os
import shutil

import pytest

import fiona


logging.basicConfig(level=logging.DEBUG)


@pytest.fixture(scope='function')
def gre_shp_cp1252():
    """A tempdir containing copies of gre.* files, .cpg set to cp1252

    The shapefile attributes are in fact utf-8 encoded.
    """
    test_files = glob(os.path.join(os.path.dirname(__file__), 'data/gre.*'))
    tmpdir = pytest.ensuretemp('tests/data')
    for filename in test_files:
        shutil.copy(filename, str(tmpdir))
    tmpdir.join('gre.cpg').write('cp1252')
    return tmpdir


def test_broken_encoding(gre_shp_cp1252):
    """Reading as cp1252 mis-encodes a Russian name"""
    shapefile = str(gre_shp_cp1252.join('gre.shp'))
    with fiona.open(shapefile) as src:
        assert next(src)['properties']['name_ru'] == 'Ð“Ñ€ÐµÐ½Ð°Ð´Ð°'


def test_override_encoding(gre_shp_cp1252):
    """utf-8 override succeeds"""
    shapefile = str(gre_shp_cp1252.join('gre.shp'))
    with fiona.open(shapefile, encoding='utf-8') as src:
        assert next(src)['properties']['name_ru'] == 'Гренада'
