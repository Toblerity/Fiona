import json
import os
import tempfile

import click
from click.testing import CliRunner

import fiona
from fiona.fio import fio


input_seq = u'\x1e{"geometry": {"coordinates": [[[100094.81257811641, 6684726.008762141], [98548.69617048775, 6684924.5976624405], [87664.09899970173, 6686905.046363058], [86952.87877302397, 6687103.688267614], [85283.08641112497, 6688045.252446961], [84540.91936600611, 6688936.450241844], [82963.96745943041, 6691364.418923092], [82469.15232285221, 6692405.682380612], [81819.82573305666, 6693843.436658373], [82438.31682390235, 6697660.772804541], [83365.94214068248, 6700140.454427341], [84633.75982132941, 6700339.2401707815], [88066.07368095664, 6699495.907563213], [99321.69871455646, 6696173.432660581], [100651.41003208276, 6695726.6230187025], [101177.06066760799, 6695379.438652324], [103588.9087551346, 6692158.022348123], [104269.2934828625, 6691215.983683517], [105073.24284537231, 6689679.516414698], [105475.21752662722, 6688540.508853204], [105506.16434506832, 6687846.5876325965], [105413.32388974504, 6687203.011032262], [104918.6200726609, 6686856.189040878], [100713.19234947088, 6684875.573921225], [100094.81257811641, 6684726.008762141]]], "type": "Polygon"}, "id": "0", "properties": {"AREA": 244820.0, "CAT": 232.0, "CNTRY_NAME": "United Kingdom", "FIPS_CNTRY": "UK", "POP_CNTRY": 60270708.0}, "type": "Feature"}\n\x1e{"geometry": {"coordinates": [[[100094.81257811641, 6684726.008762141], [98548.69617048775, 6684924.5976624405], [87664.09899970173, 6686905.046363058], [86952.87877302397, 6687103.688267614], [85283.08641112497, 6688045.252446961], [84540.91936600611, 6688936.450241844], [82963.96745943041, 6691364.418923092], [82469.15232285221, 6692405.682380612], [81819.82573305666, 6693843.436658373], [82438.31682390235, 6697660.772804541], [83365.94214068248, 6700140.454427341], [84633.75982132941, 6700339.2401707815], [88066.07368095664, 6699495.907563213], [99321.69871455646, 6696173.432660581], [100651.41003208276, 6695726.6230187025], [101177.06066760799, 6695379.438652324], [103588.9087551346, 6692158.022348123], [104269.2934828625, 6691215.983683517], [105073.24284537231, 6689679.516414698], [105475.21752662722, 6688540.508853204], [105506.16434506832, 6687846.5876325965], [105413.32388974504, 6687203.011032262], [104918.6200726609, 6686856.189040878], [100713.19234947088, 6684875.573921225], [100094.81257811641, 6684726.008762141]]], "type": "Polygon"}, "id": "0", "properties": {"AREA": 244820.0, "CAT": 232.0, "CNTRY_NAME": "United Kingdom", "FIPS_CNTRY": "UK", "POP_CNTRY": 60270708.0}, "type": "Feature"}\n'

input_collection = u'\x1e{"features": [{"geometry": {"coordinates": [[[100094.81257811641, 6684726.008762141], [98548.69617048775, 6684924.5976624405], [87664.09899970173, 6686905.046363058], [86952.87877302397, 6687103.688267614], [85283.08641112497, 6688045.252446961], [84540.91936600611, 6688936.450241844], [82963.96745943041, 6691364.418923092], [82469.15232285221, 6692405.682380612], [81819.82573305666, 6693843.436658373], [82438.31682390235, 6697660.772804541], [83365.94214068248, 6700140.454427341], [84633.75982132941, 6700339.2401707815], [88066.07368095664, 6699495.907563213], [99321.69871455646, 6696173.432660581], [100651.41003208276, 6695726.6230187025], [101177.06066760799, 6695379.438652324], [103588.9087551346, 6692158.022348123], [104269.2934828625, 6691215.983683517], [105073.24284537231, 6689679.516414698], [105475.21752662722, 6688540.508853204], [105506.16434506832, 6687846.5876325965], [105413.32388974504, 6687203.011032262], [104918.6200726609, 6686856.189040878], [100713.19234947088, 6684875.573921225], [100094.81257811641, 6684726.008762141]]], "type": "Polygon"}, "id": "0", "properties": {"AREA": 244820.0, "CAT": 232.0, "CNTRY_NAME": "United Kingdom", "FIPS_CNTRY": "UK", "POP_CNTRY": 60270708.0}, "type": "Feature"}], "type": "FeatureCollection" }\n'


def test_load_err():
    runner = CliRunner()
    result = runner.invoke(
        fio.load,
        ['-f', 'Shapefile'],
        open('docs/data/test_uk.json').read(),
        catch_exceptions=False)
    assert result.exit_code == 2


def test_load_exception(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        fio.load,
        ['-f', 'Shapefile', tmpfile],
        '42',
        catch_exceptions=False)
    assert result.exit_code == 1


def test_load(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        fio.load,
        ['-f', 'Shapefile', tmpfile],
        open('docs/data/test_uk.json').read(),
        catch_exceptions=False)
    assert result.exit_code == 0
    assert len(fiona.open(tmpfile)) == 48


def test_load_seq(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        fio.load,
        ['-f', 'Shapefile', tmpfile],
        input_seq,
        catch_exceptions=False)
    assert result.exit_code == 0
    assert len(fiona.open(tmpfile)) == 2


def test_load_seq_no_rs(tmpdir=None):
    if tmpdir is None:
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.shp')
    else:
        tmpfile = str(tmpdir.join('test.shp'))
    runner = CliRunner()
    result = runner.invoke(
        fio.load,
        ['-f', 'Shapefile', '--x-json-seq', tmpfile],
        input_seq.replace('\x1e', ''),
        catch_exceptions=False)
    assert result.exit_code == 0
    assert len(fiona.open(tmpfile)) == 2
