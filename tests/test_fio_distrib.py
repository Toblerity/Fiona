"""Unittests for $ fio distrib"""


from click.testing import CliRunner

from fiona.fio import distrib

from .fixtures import feature_collection
from .fixtures import feature_collection_pp


def test_distrib():
    runner = CliRunner()
    result = runner.invoke(distrib.distrib, [], feature_collection_pp)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2


def test_distrib_no_rs():
    runner = CliRunner()
    result = runner.invoke(distrib.distrib, [], feature_collection)
    assert result.exit_code == 0
    assert result.output.count('"Feature"') == 2
