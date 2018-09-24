"""Tests for `$ fio cat`."""


import os
import pytest
from click.testing import CliRunner

from fiona.fio.main import main_group
from fiona.fio import cat

DATA_DIR = os.path.join('tests', 'data')
WILDSHP = os.path.join(DATA_DIR, 'coutwildrnp.shp')


def test_one():
    runner = CliRunner()
    result = runner.invoke(main_group, ['cat', WILDSHP])
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 67


def test_two():
    runner = CliRunner()
    result = runner.invoke(main_group, ['cat', WILDSHP, WILDSHP])
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 134


def test_bbox_no():
    runner = CliRunner()
    result = runner.invoke(
        main_group,
        ['cat', WILDSHP, '--bbox', '0,10,80,20'],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output == ""


def test_bbox_yes():
    runner = CliRunner()
    result = runner.invoke(
        main_group,
        ['cat', WILDSHP, '--bbox', '-109,37,-107,39'],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 19


def test_bbox_yes_two_files():
    runner = CliRunner()
    result = runner.invoke(
        main_group,
        ['cat', WILDSHP, WILDSHP, '--bbox', '-109,37,-107,39'],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 38


def test_bbox_json_yes():
    runner = CliRunner()
    result = runner.invoke(
        main_group,
        ['cat', WILDSHP, '--bbox', '[-109,37,-107,39]'],
        catch_exceptions=False)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 19


def test_multi_layer():
    layerdef = "1:coutwildrnp,1:coutwildrnp"
    runner = CliRunner()
    result = runner.invoke(
        main_group, ['cat', '--layer', layerdef, DATA_DIR])
    assert result.output.count('"Feature"') == 134


def test_multi_layer_fail():
    runner = CliRunner()
    result = runner.invoke(main_group, ['cat', '--layer', '200000:coutlildrnp',
                           DATA_DIR])
    assert result.exit_code != 0


def test_vfs(path_coutwildrnp_zip):
    runner = CliRunner()
    result = runner.invoke(main_group, [
        'cat', 'zip://{}'.format(path_coutwildrnp_zip)])
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 67
