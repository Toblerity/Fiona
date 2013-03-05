
from fiona import crs

def test_proj_keys():
    assert len(crs.all_proj_keys) == 85
    assert 'proj' in crs.all_proj_keys
    assert 'no_mayo' in crs.all_proj_keys

def test_from_string():
    # A PROJ.4 string with extra whitespace
    val = crs.from_string(
        " +proj=longlat +ellps=WGS84 +datum=WGS84  +no_defs +foo  " )
    assert len(val.items()) == 4
    assert val['proj'] == 'longlat'
    assert val['ellps'] == 'WGS84'
    assert val['datum'] == 'WGS84'
    assert val['no_defs'] == True
    assert 'foo' not in val

def test_to_string():
    # Make a string from a mapping with a few bogus items
    val = {
        'proj': 'longlat', 'ellps': 'WGS84', 'datum': 'WGS84', 
        'no_defs': True, 'foo': True, 'axis': False, 'belgium': [1,2] }
    assert crs.to_string(
        val) == "+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat"

def test_from_epsg():
    val = crs.from_epsg(4326)
    assert val['init'] == "epsg:4326"
    assert val['no_defs'] == True

