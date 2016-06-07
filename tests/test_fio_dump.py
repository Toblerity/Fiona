"""Unittests for $ fio dump"""


from click.testing import CliRunner

from fiona.fio import dump


WILDSHP = 'tests/data/coutwildrnp.shp'
TESTGPX = 'tests/data/test_gpx.gpx'


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
