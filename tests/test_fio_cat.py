"""Tests for `$ fio cat`."""


import sys
import os
import pytest
from click.testing import CliRunner

from fiona.fio import cat


WILDSHP = 'tests/data/coutwildrnp.shp'
FIXME_WINDOWS = sys.platform.startswith('win')
DATA_DIR = os.path.join('tests', 'data')


@pytest.mark.skipif(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Please look into why this test is not working.")
def test_one():
    runner = CliRunner()
    result = runner.invoke(cat.cat, [WILDSHP])
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 67


@pytest.mark.skipif(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Please look into why this test is not working.")
def test_two():
    runner = CliRunner()
    result = runner.invoke(cat.cat, [WILDSHP, WILDSHP])
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 134


@pytest.mark.skipif(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Please look into why this test is not working.")
def test_bbox_no():
    runner = CliRunner()
    result = runner.invoke(
        cat.cat,
        [WILDSHP, '--bbox', '0,10,80,20'],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output == ""


@pytest.mark.skipif(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Please look into why this test is not working.")
def test_bbox_yes():
    runner = CliRunner()
    result = runner.invoke(
        cat.cat,
        [WILDSHP, '--bbox', '-109,37,-107,39'],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 19


@pytest.mark.skipif(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Please look into why this test is not working.")
def test_bbox_json_yes():
    runner = CliRunner()
    result = runner.invoke(
        cat.cat,
        [WILDSHP, '--bbox', '[-109,37,-107,39]'],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 19


def test_multi_layer():
    layerdef = "1:coutwildrnp,1:coutwildrnp"
    runner = CliRunner()
    result = runner.invoke(
        cat.cat, ['--layer', layerdef, DATA_DIR])
    assert result.output.count('"Feature"') == 134


def test_multi_layer_fail():
    runner = CliRunner()
    result = runner.invoke(cat.cat, '--layer'
                           '200000:coutlildrnp',
                           DATA_DIR)
    assert result.exit_code == 1


def test_vfs(path_coutwildrnp_zip):
    runner = CliRunner()
    result = runner.invoke(cat.cat, [
        'zip://{}'.format(path_coutwildrnp_zip)])
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 67
