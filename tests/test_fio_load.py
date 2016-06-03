import json
import os
import shutil
import sys
import tempfile
import unittest

from click.testing import CliRunner

import fiona
from fiona.fio.main import main_group

from .fixtures import (
    feature_collection, feature_seq, feature_seq_pp_rs)

FIXME_WINDOWS = sys.platform.startswith('win')

def test_err():
    runner = CliRunner()
    result = runner.invoke(
        main_group, ['load'], '', catch_exceptions=False)
    assert result.exit_code == 2


def test_exception(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        main_group, ['load', '-f', 'Shapefile', tmpfile], '42', catch_exceptions=False)
    assert result.exit_code == 1

@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_collection(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        main_group, ['load', '-f', 'Shapefile', tmpfile], feature_collection)
    assert result.exit_code == 0
    assert len(fiona.open(tmpfile)) == 2


@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_seq_rs(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        main_group, ['load', '-f', 'Shapefile', tmpfile], feature_seq_pp_rs)
    assert result.exit_code == 0
    assert len(fiona.open(tmpfile)) == 2


@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_seq_no_rs(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        main_group, ['load', '-f', 'Shapefile', '--sequence', tmpfile], feature_seq)
    assert result.exit_code == 0
    assert len(fiona.open(tmpfile)) == 2


@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_dst_crs_default_to_src_crs(tmpdir=None):
    # When --dst-crs is not given default to --src-crs.
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        main_group, [
            'load', '--src-crs', 'EPSG:32617', '-f', 'Shapefile', '--sequence', tmpfile
        ], feature_seq)
    assert result.exit_code == 0
    with fiona.open(tmpfile) as src:
        assert src.crs == {'init': 'epsg:32617'}
        assert len(src) == len(feature_seq.splitlines())


@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_different_crs(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        main_group, [
            'load', '--src-crs', 'EPSG:32617', '--dst-crs', 'EPSG:32610',
            '-f', 'Shapefile', '--sequence', tmpfile
        ], feature_seq)
    assert result.exit_code == 0
    with fiona.open(tmpfile) as src:
        assert src.crs == {'init': 'epsg:32610'}
        assert len(src) == len(feature_seq.splitlines())


@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_dst_crs_no_src(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        main_group, [
            'load', '--dst-crs', 'EPSG:32610', '-f', 'Shapefile', '--sequence', tmpfile
        ], feature_seq)
    assert result.exit_code == 0
    with fiona.open(tmpfile) as src:
        assert src.crs == {'init': 'epsg:32610'}
        assert len(src) == len(feature_seq.splitlines())


@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_fio_load_layer():

    tmpdir = tempfile.mkdtemp()
    try:
        feature = {
            'type': 'Feature',
            'properties': {'key': 'value'},
            'geometry': {
                'type': 'Point',
                'coordinates': (5.0, 39.0)
            }
        }

        sequence = os.linesep.join(map(json.dumps, [feature, feature]))

        runner = CliRunner()
        result = runner.invoke(main_group, [
            'load',
            tmpdir,
            '--driver', 'ESRI Shapefile',
            '--src-crs', 'EPSG:4236',
            '--layer', 'test_layer',
            '--sequence'],
            input=sequence)
        assert result.exit_code == 0

        with fiona.open(tmpdir) as src:
            assert len(src) == 2
            assert src.name == 'test_layer'
            assert src.schema['geometry'] == 'Point'

    finally:
        shutil.rmtree(tmpdir)
