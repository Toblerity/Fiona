"""Unittests for $ fio dump"""

import sys
import unittest

from click.testing import CliRunner

from fiona.fio import dump


WILDSHP = 'tests/data/coutwildrnp.shp'

FIXME_WINDOWS = sys.platform.startswith('win')

@unittest.skipIf(FIXME_WINDOWS, 
                 reason="FIXME on Windows. Please look into why this test is not working.")
def test_dump():
    runner = CliRunner()
    result = runner.invoke(dump.dump, [WILDSHP])
    assert result.exit_code == 0
    assert '"FeatureCollection"' in result.output
