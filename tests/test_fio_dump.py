"""Unittests for $ fio dump"""


import json
import sys

from click.testing import CliRunner
import pytest

import fiona
from fiona.fio import dump
from fiona.fio.main import main_group


FIXME_WINDOWS = sys.platform.startswith('win')


@pytest.mark.skipif(
    FIXME_WINDOWS,
    reason="FIXME on Windows. Please look into why this test is not working.")
def test_dump(path_coutwildrnp_shp):
    runner = CliRunner()
    result = runner.invoke(dump.dump, [path_coutwildrnp_shp])
    assert result.exit_code == 0
    assert '"FeatureCollection"' in result.output


def test_dump_layer(path_gpx):
    for layer in ('routes', '1'):
        runner = CliRunner()
        result = runner.invoke(dump.dump, [path_gpx, '--layer', layer])
        assert result.exit_code == 0
        assert '"FeatureCollection"' in result.output


def test_dump_layer_vfs(path_coutwildrnp_zip):
    path = 'zip://{}'.format(path_coutwildrnp_zip)
    result = CliRunner().invoke(main_group, ['dump', path])
    assert result.exit_code == 0
    loaded = json.loads(result.output)
    with fiona.open(path) as src:
        assert len(loaded['features']) == len(src)
        assert len(loaded['features']) > 0
