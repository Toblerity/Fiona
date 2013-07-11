
from six import text_type
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
