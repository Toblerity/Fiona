from pkg_resources import iter_entry_points
import re

from click.testing import CliRunner

from fiona.fio.main import main_group


WILDSHP = 'tests/data/coutwildrnp.shp'


def test_info_json():
    runner = CliRunner()
    result = runner.invoke(main_group, ['info', WILDSHP])
    assert result.exit_code == 0
    assert '"count": 67' in result.output
    assert '"crs": "EPSG:4326"' in result.output
    assert '"driver": "ESRI Shapefile"' in result.output


def test_info_count():
    runner = CliRunner()
    result = runner.invoke(main_group, ['info', '--count', WILDSHP])
    assert result.exit_code == 0
    assert result.output == "67\n"


def test_info_bounds():
    runner = CliRunner()
    result = runner.invoke(main_group, ['info', '--bounds', WILDSHP])
    assert result.exit_code == 0
    assert len(re.findall(r'\d*\.\d*', result.output)) == 4


def test_all_registered():
    # Make sure all the subcommands are actually registered to the main CLI group
    for ep in iter_entry_points('fiona.fio_commands'):
        assert ep.name in main_group.commands
