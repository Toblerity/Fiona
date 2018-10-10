"""Tests for `$ fio filter`."""

from fiona.fio.main import main_group


def test_fail(runner):
    result = runner.invoke(main_group, ['filter',
        "f.properties.test > 5"
    ], "{'type': 'no_properties'}")
    assert result.exit_code == 1


def test_seq(feature_seq, runner):

    result = runner.invoke(main_group, ['filter',
        "f.properties.AREA > 0.01"], feature_seq)
    assert result.exit_code == 0
    assert result.output.count('Feature') == 2

    result = runner.invoke(main_group, ['filter',
        "f.properties.AREA > 0.015"], feature_seq)
    assert result.exit_code == 0
    assert result.output.count('Feature') == 1

    result = runner.invoke(main_group, ['filter',
        "f.properties.AREA > 0.02"], feature_seq)
    assert result.exit_code == 0
    assert result.output.count('Feature') == 0
