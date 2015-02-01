import json
import re

import click
from click.testing import CliRunner

from fiona.fio import bounds

from .fixtures import (
    feature_collection, feature_collection_pp, feature_seq, feature_seq_pp_rs)


def test_fail():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, [], '5')
    assert result.exit_code == 1


def test_seq():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, [], feature_seq)
    assert result.exit_code == 0
    assert result.output.count('[') == result.output.count(']') == 2
    assert len(re.findall(r'\d*\.\d*', result.output)) == 8


def test_seq_rs():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, [], feature_seq_pp_rs)
    assert result.exit_code == 0
    assert result.output.count('[') == result.output.count(']') == 2
    assert len(re.findall(r'\d*\.\d*', result.output)) == 8


def test_precision():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--precision', 1], feature_seq)
    assert result.exit_code == 0
    assert result.output.count('[') == result.output.count(']') == 2
    assert len(re.findall(r'\d*\.\d{1}\D', result.output)) == 8


def test_explode():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--explode'], feature_collection)
    assert result.exit_code == 0
    assert result.output.count('[') == result.output.count(']') == 2
    assert len(re.findall(r'\d*\.\d*', result.output)) == 8


def test_explode_pp():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--explode'], feature_collection_pp)
    assert result.exit_code == 0
    assert result.output.count('[') == result.output.count(']') == 2
    assert len(re.findall(r'\d*\.\d*', result.output)) == 8


def test_with_id():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--with-id'], feature_seq)
    assert result.exit_code == 0
    assert result.output.count('id') == result.output.count('bbox') == 2


def test_explode_with_id():
    runner = CliRunner()
    result = runner.invoke(
        bounds.bounds, ['--explode', '--with-id'], feature_collection)
    assert result.exit_code == 0
    assert result.output.count('id') == result.output.count('bbox') == 2


def test_with_obj():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--with-obj'], feature_seq)
    assert result.exit_code == 0
    assert result.output.count('geometry') == result.output.count('bbox') == 2


def test_bounds_explode_with_obj():
    runner = CliRunner()
    result = runner.invoke(
        bounds.bounds, ['--explode', '--with-obj'], feature_collection)
    assert result.exit_code == 0
    assert result.output.count('geometry') == result.output.count('bbox') == 2


def test_explode_output_rs():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--explode', '--rs'], feature_collection)
    assert result.exit_code == 0
    assert result.output.count(u'\u001e') == 2
    assert result.output.count('[') == result.output.count(']') == 2
    assert len(re.findall(r'\d*\.\d*', result.output)) == 8
