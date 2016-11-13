"""Tests for `$ fio distrib`."""


from click.testing import CliRunner

from fiona.fio import distrib


def test_distrib(feature_collection_pp):
    runner = CliRunner()
    result = runner.invoke(distrib.distrib, [], feature_collection_pp)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2


def test_distrib_no_rs(feature_collection):
    runner = CliRunner()
    result = runner.invoke(distrib.distrib, [], feature_collection)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2
