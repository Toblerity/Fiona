import json
import os.path
from six import text_type
import tempfile

import fiona
from fiona import prop_type, prop_width
from fiona.rfc3339 import FionaDateType


def test_width_str():
    assert prop_width('str:254') == 254
    assert prop_width('str') == 80


def test_width_other():
    assert prop_width('int') == None
    assert prop_width('float') == None
    assert prop_width('date') == None


def test_types():
    assert prop_type('str:254') == text_type
    assert prop_type('str') == text_type
    assert prop_type('int') == type(0)
    assert prop_type('float') == type(0.0)
    assert prop_type('date') == FionaDateType


def test_read_json_object_properties():
    """JSON object properties are properly serialized"""
    data = """
{
  "type": "FeatureCollection",
  "features": [
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              87.33588,
              43.53139
            ],
            [
              87.33588,
              45.66894
            ],
            [
              90.27542,
              45.66894
            ],
            [
              90.27542,
              43.53139
            ],
            [
              87.33588,
              43.53139
            ]
          ]
        ]
      },
      "type": "Feature",
      "properties": {
        "upperLeftCoordinate": {
          "latitude": 45.66894,
          "longitude": 87.91166
        },
        "tricky": "{gotcha"
      }
    }
  ]
}
"""
    tmpdir = tempfile.mkdtemp()
    filename = os.path.join(tmpdir, 'test.json')

    with open(filename, 'w') as f:
        f.write(data)

    with fiona.open(filename) as src:
        ftr = next(src)
        props = ftr['properties']
        assert props['upperLeftCoordinate']['latitude'] == 45.66894
        assert props['upperLeftCoordinate']['longitude'] == 87.91166
        assert props['tricky'] == "{gotcha"


def test_write_json_object_properties():
    """Python object properties are properly serialized"""
    data = """
{
  "type": "FeatureCollection",
  "features": [
    {
      "geometry": {
        "type": "Polygon",
        "coordinates": [
          [
            [
              87.33588,
              43.53139
            ],
            [
              87.33588,
              45.66894
            ],
            [
              90.27542,
              45.66894
            ],
            [
              90.27542,
              43.53139
            ],
            [
              87.33588,
              43.53139
            ]
          ]
        ]
      },
      "type": "Feature",
      "properties": {
        "upperLeftCoordinate": {
          "latitude": 45.66894,
          "longitude": 87.91166
        },
        "tricky": "{gotcha"
      }
    }
  ]
}
"""
    data = json.loads(data)['features'][0]
    tmpdir = tempfile.mkdtemp()
    filename = os.path.join(tmpdir, 'test.json')
    with fiona.open(
            filename, 'w',
            driver='GeoJSON',
            schema={
                'geometry': 'Polygon',
                'properties': {'upperLeftCoordinate': 'str', 'tricky': 'str'}}
            ) as dst:
        dst.write(data)

    with fiona.open(filename) as src:
        ftr = next(src)
        props = ftr['properties']
        assert props['upperLeftCoordinate']['latitude'] == 45.66894
        assert props['upperLeftCoordinate']['longitude'] == 87.91166
        assert props['tricky'] == "{gotcha"
