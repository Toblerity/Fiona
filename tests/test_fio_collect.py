"""Unittests for $ fio collect"""


import json
import sys
import unittest

from click.testing import CliRunner

from fiona.fio import collect

from .fixtures import feature_seq
from .fixtures import feature_seq_pp_rs

FIXME_WINDOWS = sys.platform.startswith('win')

@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_collect_rs():
    runner = CliRunner()
    result = runner.invoke(
        collect.collect,
        ['--src-crs', 'EPSG:3857'],
        feature_seq_pp_rs,
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2


@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_collect_no_rs():
    runner = CliRunner()
    result = runner.invoke(
        collect.collect,
        ['--src-crs', 'EPSG:3857'],
        feature_seq,
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2


def test_collect_ld():
    runner = CliRunner()
    result = runner.invoke(
        collect.collect,
        ['--with-ld-context', '--add-ld-context-item', 'foo=bar'],
        feature_seq,
        catch_exceptions=False)
    assert result.exit_code == 0
    assert '"@context": {' in result.output
    assert '"foo": "bar"' in result.output


def test_collect_rec_buffered():
    runner = CliRunner()
    result = runner.invoke(collect.collect, ['--record-buffered'], feature_seq)
    assert result.exit_code == 0
    assert '"FeatureCollection"' in result.output


def test_collect_noparse():
    runner = CliRunner()
    result = runner.invoke(
        collect.collect,
        ['--no-parse'],
        feature_seq,
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2
    assert len(json.loads(result.output)['features']) == 2


def test_collect_noparse_records():
    runner = CliRunner()
    result = runner.invoke(
        collect.collect,
        ['--no-parse', '--record-buffered'],
        feature_seq,
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2
    assert len(json.loads(result.output)['features']) == 2


def test_collect_src_crs():
    runner = CliRunner()
    result = runner.invoke(
        collect.collect,
        ['--no-parse', '--src-crs', 'epsg:4326'],
        feature_seq,
        catch_exceptions=False)
    assert result.exit_code == 2


def test_collect_noparse_rs():
    runner = CliRunner()
    result = runner.invoke(
        collect.collect,
        ['--no-parse'],
        feature_seq_pp_rs,
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2
    assert len(json.loads(result.output)['features']) == 2
