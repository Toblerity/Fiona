from __future__ import division
import json

from click.testing import CliRunner

from fiona.fio.calc import calc
from .fixtures import feature_seq


def test_fail():
    runner = CliRunner()
    result = runner.invoke(calc,
                           ["TEST", "f.properties.test > 5"],
                           '{"type": "no_properties"}')
    assert result.exit_code == 1


def _load(output):
    features = []
    for x in output.splitlines():
        try:
            features.append(json.loads(x))
        except:
            pass  # nosetests puts some debugging garbage to stdout
    return features


def test_calc_seq():
    runner = CliRunner()

    result = runner.invoke(calc,
                           ["TEST", "f.properties.AREA / f.properties.PERIMETER"],
                           feature_seq)
    assert result.exit_code == 0

    feats = _load(result.output)
    assert len(feats) == 2
    for feat in feats:
        assert feat['properties']['TEST'] == \
            feat['properties']['AREA'] / feat['properties']['PERIMETER']


def test_bool_seq():
    runner = CliRunner()

    result = runner.invoke(calc,
                           ["TEST", "f.properties.AREA > 0.015"],
                           feature_seq)
    assert result.exit_code == 0
    feats = _load(result.output)
    assert len(feats) == 2
    assert feats[0]['properties']['TEST'] == True
    assert feats[1]['properties']['TEST'] == False


def test_existing_property():
    runner = CliRunner()

    result = runner.invoke(calc,
                           ["AREA", "f.properties.AREA * 2"],
                           feature_seq)
    assert result.exit_code == 1

    result = runner.invoke(calc,
                           ["--overwrite", "AREA", "f.properties.AREA * 2"],
                           feature_seq)
    assert result.exit_code == 0
    feats = _load(result.output)
    assert len(feats) == 2
    for feat in feats:
        assert 'AREA' in feat['properties']
