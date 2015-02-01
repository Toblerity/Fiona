import json

import click
from click.testing import CliRunner

from fiona.fio import cat

from .fixtures import (
    feature_collection, feature_collection_pp, feature_seq, feature_seq_pp_rs)


WILDSHP = 'tests/data/coutwildrnp.shp'


def test_one():
    runner = CliRunner()
    result = runner.invoke(cat.cat, [WILDSHP])
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 67


def test_two():
    runner = CliRunner()
    result = runner.invoke(cat.cat, [WILDSHP, WILDSHP])
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 134


def test_bbox_no():
    runner = CliRunner()
    result = runner.invoke(
        cat.cat,
        [WILDSHP, '--bbox', '0,10,80,20'],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output == ""


def test_bbox_yes():
    runner = CliRunner()
    result = runner.invoke(
        cat.cat,
        [WILDSHP, '--bbox', '-109,37,-107,39'],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 19


def test_bbox_json_yes():
    runner = CliRunner()
    result = runner.invoke(
        cat.cat,
        [WILDSHP, '--bbox', '[-109,37,-107,39]'],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 19


def test_collect_rs():
    runner = CliRunner()
    result = runner.invoke(
        cat.collect,
        ['--src_crs', 'EPSG:3857'],
        feature_seq_pp_rs,
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2


def test_collect_no_rs():
    runner = CliRunner()
    result = runner.invoke(
        cat.collect,
        ['--src_crs', 'EPSG:3857'],
        feature_seq,
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2


def test_collect_ld():
    runner = CliRunner()
    result = runner.invoke(
        cat.collect,
        ['--with-ld-context', '--add-ld-context-item', 'foo=bar'],
        feature_seq,
        catch_exceptions=False)
    assert result.exit_code == 0
    assert '"@context": {' in result.output
    assert '"foo": "bar"' in result.output


def test_collect_rec_buffered():
    runner = CliRunner()
    result = runner.invoke(cat.collect, ['--record-buffered'], feature_seq)
    assert result.exit_code == 0
    assert '"FeatureCollection"' in result.output


def test_distrib():
    runner = CliRunner()
    result = runner.invoke(cat.distrib, [], feature_collection_pp)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2


def test_distrib_no_rs():
    runner = CliRunner()
    result = runner.invoke(cat.distrib, [], feature_collection)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2


def test_dump():
    runner = CliRunner()
    result = runner.invoke(cat.dump, [WILDSHP])
    assert result.exit_code == 0
    assert '"FeatureCollection"' in result.output
