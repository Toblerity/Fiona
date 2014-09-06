import json
import subprocess


def test_cli_info_json():
    result = subprocess.check_output(
        'fio info docs/data/test_uk.shp',
        shell=True)
    text = result.decode('utf-8').strip()
    assert json.loads(text)['count'] == 48


def test_cli_info_count():
    result = subprocess.check_output(
        'fio info docs/data/test_uk.shp --count',
        shell=True)
    assert result.decode('utf-8').strip() == '48'


def test_cli_info_bounds():
    result = subprocess.check_output(
        'fio info docs/data/test_uk.shp --bounds',
        shell=True)
    assert result.decode('utf-8').strip() == (
        '-8.621389 49.911659 1.749444 60.844444')
