import json
import re

import click
from click.testing import CliRunner

from fiona.fio import fio


WILDSHP = 'tests/data/coutwildrnp.shp'


def test_info_json():
    runner = CliRunner()
    result = runner.invoke(fio.info, [WILDSHP])
    assert result.exit_code == 0
    assert '"count": 67' in result.output
    assert '"crs": "EPSG:4326"' in result.output
    assert '"driver": "ESRI Shapefile"' in result.output


def test_info_count():
    runner = CliRunner()
    result = runner.invoke(fio.info, ['--count', WILDSHP])
    assert result.exit_code == 0
    assert result.output == "67\n"


def test_info_bounds():
    runner = CliRunner()
    result = runner.invoke(fio.info, ['--bounds', WILDSHP])
    assert result.exit_code == 0
    assert len(re.findall(r'\d*\.\d*', result.output)) == 4
