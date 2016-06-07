"""Unittests for $ fio dump"""


from click.testing import CliRunner

from fiona.fio import dump


WILDSHP = 'tests/data/coutwildrnp.shp'


def test_dump():
    runner = CliRunner()
    result = runner.invoke(dump.dump, [WILDSHP])
    assert result.exit_code == 0
    assert '"FeatureCollection"' in result.output


def test_dump_layer():
    runner = CliRunner()
    for layer in ('routes', '1'):
        runner = CliRunner()
        result = runner.invoke(dump.dump, [WILDSHP, '--layer ', layer])
        assert result.exit_code == 0
        assert '"FeatureCollection"' in result.output
