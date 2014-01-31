
from fiona import crs

def test_proj_keys():
    assert len(crs.all_proj_keys) == 86
    assert 'init' in crs.all_proj_keys
    assert 'proj' in crs.all_proj_keys
    assert 'no_mayo' in crs.all_proj_keys

def test_from_string():
    # A PROJ.4 string with extra whitespace.
    val = crs.from_string(
        " +proj=longlat +ellps=WGS84 +datum=WGS84  +no_defs +foo  " )
    assert len(val.items()) == 4
    assert val['proj'] == 'longlat'
    assert val['ellps'] == 'WGS84'
    assert val['datum'] == 'WGS84'
    assert val['no_defs'] == True
    assert 'foo' not in val

def test_from_string_utm():
    # A PROJ.4 string with extra whitespace and integer UTM zone.
    val = crs.from_string(
        " +proj=utm +zone=13 +ellps=WGS84 +foo  " )
    assert len(val.items()) == 3
    assert val['proj'] == 'utm'
    assert val['ellps'] == 'WGS84'
    assert val['zone'] == 13
    assert 'foo' not in val

def test_to_string():
    # Make a string from a mapping with a few bogus items
    val = {
        'proj': 'longlat', 'ellps': 'WGS84', 'datum': 'WGS84', 
        'no_defs': True, 'foo': True, 'axis': False, 'belgium': [1,2] }
    assert crs.to_string(
        val) == "+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat"

def test_to_string_utm():
    # Make a string from a mapping with a few bogus items
    val = {
        'proj': 'utm', 'ellps': 'WGS84', 'zone': 13, 
        'no_defs': True, 'foo': True, 'axis': False, 'belgium': [1,2] }
    assert crs.to_string(
        val) == "+ellps=WGS84 +no_defs +proj=utm +zone=13"

def test_to_string_epsg():
    val = {'init': 'epsg:4326', 'no_defs': True}
    assert crs.to_string(val) == "+init=epsg:4326 +no_defs"

def test_from_epsg():
    val = crs.from_epsg(4326)
    assert val['init'] == "epsg:4326"
    assert val['no_defs'] == True

def test_from_epsg_neg():
    try:
        val = crs.from_epsg(-1)
    except ValueError:
        pass
    except:
        raise

def test_to_string_unicode():
    # See issue #83.
    val = crs.to_string({
        u'units': u'm', 
        u'no_defs': True, 
        u'datum': u'NAD83', 
        u'proj': u'utm', 
        u'zone': 16})
    assert 'NAD83' in val
