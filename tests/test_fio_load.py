import os
import tempfile

from click.testing import CliRunner

import fiona
from fiona.fio.main import main_group

from .fixtures import (
    feature_collection, feature_seq, feature_seq_pp_rs)


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
