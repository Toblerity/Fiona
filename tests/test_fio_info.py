import json
from pkg_resources import iter_entry_points
import re
import sys
import unittest

from click.testing import CliRunner

from fiona.fio.main import main_group


WILDSHP = 'tests/data/coutwildrnp.shp'

FIXME_WINDOWS = sys.platform.startswith('win')

@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_info_json():
    runner = CliRunner()
    result = runner.invoke(main_group, ['info', WILDSHP])
    assert result.exit_code == 0
    assert '"count": 67' in result.output
    assert '"crs": "EPSG:4326"' in result.output
    assert '"driver": "ESRI Shapefile"' in result.output
    assert '"name": "coutwildrnp"' in result.output

@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_info_count():
    runner = CliRunner()
    result = runner.invoke(main_group, ['info', '--count', WILDSHP])
    assert result.exit_code == 0
    assert result.output == "67\n"

@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_info_bounds():
    runner = CliRunner()
    result = runner.invoke(main_group, ['info', '--bounds', WILDSHP])
    assert result.exit_code == 0
    assert len(re.findall(r'\d*\.\d*', result.output)) == 4


def test_all_registered():
    # Make sure all the subcommands are actually registered to the main CLI group
    for ep in iter_entry_points('fiona.fio_commands'):
        assert ep.name in main_group.commands


def _filter_info_warning(lines):
    """$ fio info can issue a RuntimeWarning, but click adds stderr to stdout
    so we have to filter it out before decoding JSON lines."""
    lines = list(filter(lambda x: 'RuntimeWarning' not in x, lines))
    return lines


@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_info_no_count():
    """Make sure we can still get a `$ fio info` report on datasources that do
    not support feature counting, AKA `len(collection)`.
    """
    runner = CliRunner()
    result = runner.invoke(main_group, ['info', 'tests/data/test_gpx.gpx'])
    assert result.exit_code == 0
    lines = _filter_info_warning(result.output.splitlines())
    assert len(lines) == 1, "First line is warning & second is JSON.  No more."
    assert json.loads(lines[0])['count'] is None


@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_info_layer():
    for layer in ('routes', '1'):
        runner = CliRunner()
        result = runner.invoke(main_group, [
            'info',
            'tests/data/test_gpx.gpx',
            '--layer', layer])
        print(result.output)
        assert result.exit_code == 0
        lines = _filter_info_warning(result.output.splitlines())
        assert len(lines) == 1, "1st line is warning & 2nd is JSON - no more."
        assert json.loads(lines[0])['name'] == 'routes'
