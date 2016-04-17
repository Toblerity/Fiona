import click
from click.testing import CliRunner
import pytest

from fiona.fio import info
from fiona.fio.options import validate_vfs, validate_input_path


class MockContext:
    def __init__(self):
        self.obj = {}


def test_validate_vfs_null():
    ctx = MockContext()
    assert validate_vfs(ctx, None, None) is None
    assert not ctx.obj['vfs']


def test_validate_vfs_malformed():
    with pytest.raises(click.BadParameter):
        validate_vfs(None, None, 'foobar')


def test_validate_vfs_invalid_scheme():
    with pytest.raises(click.BadParameter):
        validate_vfs(None, None, 'lol://wut')


def test_validate_vfs_nonexistent_path():
    with pytest.raises(click.BadParameter):
        validate_vfs(None, None, 'zip://wut')


def test_validate_vfs_proper():
    ctx = MockContext()
    assert validate_vfs(
        ctx, None, 'zip://tests/data/coutwildrnp.zip'
        ) == 'zip://tests/data/coutwildrnp.zip'
    assert ctx.obj['vfs']


def test_validate_input_nonexistant():
    with pytest.raises(click.BadParameter):
        validate_input_path(MockContext(), None, 'wut')


def test_validate_input_vfs():
    ctx = MockContext()
    ctx.obj['vfs'] = 'foo'
    assert validate_input_path(ctx, None, 'bar') == 'bar'


def test_bad_vfs():
    runner = CliRunner()
    result = runner.invoke(info.info, ['--vfs', 'foobar', 'foo.shp'])
    assert result.exit_code == 2
    assert "must match 'scheme://path'" in result.output


def test_wrong_scheme():
    runner = CliRunner()
    result = runner.invoke(info.info, ['--vfs', 'foo://bar', 'foo.shp'])
    assert result.exit_code == 2
