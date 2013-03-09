
from fiona import prop_width

def test_str():
    assert prop_width('str:254') == 254
    assert prop_width('str') == 80

def test_other():
    assert prop_width('int') == None
    assert prop_width('float') == None
    assert prop_width('date') == None

