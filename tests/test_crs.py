from fiona import crs, _crs


def test_proj_keys():
    assert len(crs.all_proj_keys) == 87
    assert 'init' in crs.all_proj_keys
    assert 'proj' in crs.all_proj_keys
    assert 'no_mayo' in crs.all_proj_keys


def test_from_string():
    # A PROJ.4 string with extra whitespace.
    val = crs.from_string(
        " +proj=longlat +ellps=WGS84 +datum=WGS84  +no_defs +foo  ")
    assert len(val.items()) == 4
    assert val['proj'] == 'longlat'
    assert val['ellps'] == 'WGS84'
    assert val['datum'] == 'WGS84'
    assert val['no_defs']
    assert 'foo' not in val


def test_from_string_utm():
    # A PROJ.4 string with extra whitespace and integer UTM zone.
    val = crs.from_string(
        " +proj=utm +zone=13 +ellps=WGS84 +foo  ")
    assert len(val.items()) == 3
    assert val['proj'] == 'utm'
    assert val['ellps'] == 'WGS84'
    assert val['zone'] == 13
    assert 'foo' not in val


def test_to_string():
    # Make a string from a mapping with a few bogus items
    val = {
        'proj': 'longlat', 'ellps': 'WGS84', 'datum': 'WGS84',
        'no_defs': True, 'foo': True, 'axis': False, 'belgium': [1, 2]}
    assert crs.to_string(
        val) == "+datum=WGS84 +ellps=WGS84 +no_defs +proj=longlat"


def test_to_string_utm():
    # Make a string from a mapping with a few bogus items
    val = {
        'proj': 'utm', 'ellps': 'WGS84', 'zone': 13,
        'no_defs': True, 'foo': True, 'axis': False, 'belgium': [1, 2]}
    assert crs.to_string(
        val) == "+ellps=WGS84 +no_defs +proj=utm +zone=13"


def test_to_string_epsg():
    val = {'init': 'epsg:4326', 'no_defs': True}
    assert crs.to_string(val) == "+init=epsg:4326 +no_defs"


def test_to_string_zeroval():
    # Make a string with some 0 values (e.g. esri:102017)
    val = {'proj': 'laea', 'lat_0': 90, 'lon_0': 0, 'x_0': 0, 'y_0': 0,
           'ellps': 'WGS84', 'datum': 'WGS84', 'units': 'm', 'no_defs': True}
    assert crs.to_string(val) == (
        "+datum=WGS84 +ellps=WGS84 +lat_0=90 +lon_0=0 +no_defs +proj=laea "
        "+units=m +x_0=0 +y_0=0")


def test_from_epsg():
    val = crs.from_epsg(4326)
    assert val['init'] == "epsg:4326"
    assert val['no_defs']


def test_from_epsg_neg():
    try:
        crs.from_epsg(-1)
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


def test_wktext():
    """Test +wktext parameter is preserved."""
    proj4 = ('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 '
             '+x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext '
             '+no_defs')
    assert 'wktext' in crs.from_string(proj4)


def test_towgs84():
    """+towgs84 is preserved"""
    proj4 = ('+proj=lcc +lat_1=49 +lat_2=46 +lat_0=47.5 '
             '+lon_0=13.33333333333333 +x_0=400000 +y_0=400000 +ellps=bessel '
             '+towgs84=577.326,90.129,463.919,5.137,1.474,5.297,2.4232 '
             '+units=m +wktext +no_defs')
    assert 'towgs84' in crs.from_string(proj4)


def test_towgs84_wkt():
    """+towgs84 +wktext are preserved in WKT"""
    proj4 = ('+proj=lcc +lat_1=49 +lat_2=46 +lat_0=47.5 '
             '+lon_0=13.33333333333333 +x_0=400000 +y_0=400000 +ellps=bessel '
             '+towgs84=577.326,90.129,463.919,5.137,1.474,5.297,2.4232 '
             '+units=m +wktext +no_defs')
    assert 'towgs84' in _crs.crs_to_wkt(proj4)
    assert 'wktext' in _crs.crs_to_wkt(proj4)
