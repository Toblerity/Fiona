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


def test_cli_cat():
    result = subprocess.check_output(
        'fio cat docs/data/test_uk.shp docs/data/test_uk.shp',
        shell=True)
    records = result.decode('utf-8').strip().split('\n')
    assert len(records) == 96
    for record in records:
        assert json.loads(record.strip())['type'] == 'Feature'


def test_cli_cat_rs():
    result = subprocess.check_output(
        'fio cat docs/data/test_uk.shp docs/data/test_uk.shp '
        '--indent 2 --x-json-seq-rs',
        shell=True)
    texts = result.decode('utf-8').split(u'\x1e')
    assert len(texts) == 97
    assert texts[0] == ''
    for text in texts:
        if not text:
            continue
        assert json.loads(text)['type'] == 'Feature'


def test_cli_collect():
    feature = {
        'type': 'Feature',
        'properties': {},
        'geometry': {
            'type': 'Point',
            'coordinates': [0.0, 0.0] }}
    result = subprocess.check_output(
        "echo '%s' | fio collect" % json.dumps(feature),
        shell=True)
    collection = json.loads(result.decode('utf-8'))
    assert len(collection['features']) == 1
    assert collection['features'][0] == feature


def test_cli_collect_rs():
    feature = {
        'type': 'Feature',
        'properties': {},
        'geometry': {
            'type': 'Point',
            'coordinates': [0.0, 0.0] }}
    result = subprocess.check_output(
        "printf '\036%s\n\036%s' | fio collect" % (
            json.dumps(feature, indent=2), json.dumps(feature, indent=2)),
        shell=True)
    collection = json.loads(result.decode('utf-8'))
    assert len(collection['features']) == 2
    assert collection['features'][0] == feature
