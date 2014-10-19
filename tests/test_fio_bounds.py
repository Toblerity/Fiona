import json

import click
from click.testing import CliRunner

from fiona.fio import bounds


input = u'\x1e{"geometry": {"coordinates": [[[100094.81257811641, 6684726.008762141], [98548.69617048775, 6684924.5976624405], [87664.09899970173, 6686905.046363058], [86952.87877302397, 6687103.688267614], [85283.08641112497, 6688045.252446961], [84540.91936600611, 6688936.450241844], [82963.96745943041, 6691364.418923092], [82469.15232285221, 6692405.682380612], [81819.82573305666, 6693843.436658373], [82438.31682390235, 6697660.772804541], [83365.94214068248, 6700140.454427341], [84633.75982132941, 6700339.2401707815], [88066.07368095664, 6699495.907563213], [99321.69871455646, 6696173.432660581], [100651.41003208276, 6695726.6230187025], [101177.06066760799, 6695379.438652324], [103588.9087551346, 6692158.022348123], [104269.2934828625, 6691215.983683517], [105073.24284537231, 6689679.516414698], [105475.21752662722, 6688540.508853204], [105506.16434506832, 6687846.5876325965], [105413.32388974504, 6687203.011032262], [104918.6200726609, 6686856.189040878], [100713.19234947088, 6684875.573921225], [100094.81257811641, 6684726.008762141]]], "type": "Polygon"}, "id": "0", "properties": {"AREA": 244820.0, "CAT": 232.0, "CNTRY_NAME": "United Kingdom", "FIPS_CNTRY": "UK", "POP_CNTRY": 60270708.0}, "type": "Feature"}\n'



def test_fail():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, [], '5')
    assert result.exit_code == 1


def test_bounds():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, [], input)
    assert result.exit_code == 0
    assert len(json.loads(result.output.strip())) == 4
    assert round(json.loads(result.output.strip())[0], 1) ==  81819.8


def test_bounds_precision():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--precision', 1], input)
    assert result.exit_code == 0
    assert len(json.loads(result.output.strip())) == 4
    assert json.loads(result.output.strip())[0] ==  81819.8


def test_bounds_explode():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--explode'], input)
    assert result.exit_code == 0
    assert len(json.loads(result.output.strip())) == 4
    assert round(json.loads(result.output.strip())[0], 1) ==  81819.8


def test_bounds_with_id():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--with-id'], input)
    assert result.exit_code == 0
    obj = json.loads(result.output.strip())
    assert 'id' in obj
    assert 'bbox' in obj
    assert len(obj['bbox']) == 4
    assert round(obj['bbox'][0], 1) ==  81819.8


def test_bounds_explode_with_id():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--explode', '--with-id'], input)
    assert result.exit_code == 0
    obj = json.loads(result.output.strip())
    assert 'id' in obj
    assert 'bbox' in obj
    assert len(obj['bbox']) == 4
    assert round(obj['bbox'][0], 1) ==  81819.8


def test_bounds_with_obj():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--with-obj'], input)
    assert result.exit_code == 0
    obj = json.loads(result.output.strip())
    assert 'geometry' in obj
    assert 'id' in obj
    assert 'bbox' in obj
    assert len(obj['bbox']) == 4
    assert round(obj['bbox'][0], 1) ==  81819.8


def test_bounds_explode_with_obj():
    runner = CliRunner()
    result = runner.invoke(bounds.bounds, ['--explode', '--with-obj'], input)
    assert result.exit_code == 0
    obj = json.loads(result.output.strip())
    assert 'geometry' in obj
    assert 'id' in obj
    assert 'bbox' in obj
    assert len(obj['bbox']) == 4
    assert round(obj['bbox'][0], 1) ==  81819.8
