"""Unittests for $ fio dump"""


import json
import sys

from click.testing import CliRunner
import pytest

import fiona
from fiona.fio import dump
from fiona.fio.main import main_group


WILDSHP = 'tests/data/coutwildrnp.shp'
TESTGPX = 'tests/data/test_gpx.gpx'
FIXME_WINDOWS = sys.platform.startswith('win')


@pytest.mark.skipif(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Please look into why this test is not working.")
def test_dump():
    runner = CliRunner()
    result = runner.invoke(dump.dump, [WILDSHP])
    assert result.exit_code == 0
    assert '"FeatureCollection"' in result.output


def test_dump_layer():
    for layer in ('routes', '1'):
        runner = CliRunner()
        result = runner.invoke(dump.dump, [TESTGPX, '--layer', layer])
        assert result.exit_code == 0
        assert '"FeatureCollection"' in result.output


def test_dump_layer_vfs():
    path = 'zip://tests/data/coutwildrnp.zip'
    result = CliRunner().invoke(main_group, ['dump', path])
    assert result.exit_code == 0
    loaded = json.loads(result.output)
    with fiona.open(path) as src:
        assert len(loaded['features']) == len(src)
        assert len(loaded['features']) > 0
