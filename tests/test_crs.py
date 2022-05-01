import pytest

from fiona import crs, _crs
from fiona.env import Env
from fiona.errors import CRSError

from .conftest import requires_gdal_lt_3


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


@requires_gdal_lt_3
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


@requires_gdal_lt_3
def test_towgs84_wkt():
    """+towgs84 +wktext are preserved in WKT"""
    proj4 = ('+proj=lcc +lat_1=49 +lat_2=46 +lat_0=47.5 '
             '+lon_0=13.33333333333333 +x_0=400000 +y_0=400000 +ellps=bessel '
             '+towgs84=577.326,90.129,463.919,5.137,1.474,5.297,2.4232 '
             '+units=m +wktext +no_defs')
    wkt = _crs.crs_to_wkt(proj4)
    assert 'towgs84' in wkt
    assert 'wktext' in _crs.crs_to_wkt(proj4)


@pytest.mark.parametrize("invalid_input", [
    "a random string that is invalid",
    ("a", "tuple"),
    "-48567=409 =2095"
])
def test_invalid_crs(invalid_input):
    with pytest.raises(CRSError):
        _crs.crs_to_wkt(invalid_input)


def test_custom_crs():
    class CustomCRS(object):
        def to_wkt(self):
            return (
                'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",'
                '6378137,298.257223563,AUTHORITY["EPSG","7030"]],'
                'AUTHORITY["EPSG","6326"]],PRIMEM["Greenwich",0,'
                'AUTHORITY["EPSG","8901"]],UNIT["degree",0.0174532925199433,'
                'AUTHORITY["EPSG","9122"]],AUTHORITY["EPSG","4326"]]'
            )
    assert _crs.crs_to_wkt(CustomCRS()).startswith('GEOGCS["WGS 84"')


def test_crs__version():
    target_crs = (
        'PROJCS["IaRCS_04_Sioux_City-Iowa_Falls_NAD_1983_2011_LCC_US_Feet",'
        'GEOGCS["GCS_NAD_1983_2011",DATUM["D_NAD_1983_2011",'
        'SPHEROID["GRS_1980",6378137.0,298.257222101]],'
        'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],'
        'PROJECTION["Lambert_Conformal_Conic"],'
        'PARAMETER["False_Easting",14500000.0],'
        'PARAMETER["False_Northing",8600000.0],'
        'PARAMETER["Central_Meridian",-94.83333333333333],'
        'PARAMETER["Standard_Parallel_1",42.53333333333333],'
        'PARAMETER["Standard_Parallel_2",42.53333333333333],'
        'PARAMETER["Scale_Factor",1.000045],'
        'PARAMETER["Latitude_Of_Origin",42.53333333333333],'
        'UNIT["Foot_US",0.3048006096012192]]'
    )
    assert _crs.crs_to_wkt(target_crs, wkt_version="WKT2_2018").startswith(
        'PROJCRS["IaRCS_04_Sioux_City-Iowa_Falls_NAD_1983_2011_LCC_US_Feet"'
    )


def test_crs__esri_only_wkt():
    """https://github.com/Toblerity/Fiona/issues/977"""
    target_crs = (
        'PROJCS["IaRCS_04_Sioux_City-Iowa_Falls_NAD_1983_2011_LCC_US_Feet",'
        'GEOGCS["GCS_NAD_1983_2011",DATUM["D_NAD_1983_2011",'
        'SPHEROID["GRS_1980",6378137.0,298.257222101]],'
        'PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],'
        'PROJECTION["Lambert_Conformal_Conic"],'
        'PARAMETER["False_Easting",14500000.0],'
        'PARAMETER["False_Northing",8600000.0],'
        'PARAMETER["Central_Meridian",-94.83333333333333],'
        'PARAMETER["Standard_Parallel_1",42.53333333333333],'
        'PARAMETER["Standard_Parallel_2",42.53333333333333],'
        'PARAMETER["Scale_Factor",1.000045],'
        'PARAMETER["Latitude_Of_Origin",42.53333333333333],'
        'UNIT["Foot_US",0.3048006096012192]]'
    )
    assert _crs.crs_to_wkt(target_crs).startswith(
        (
            'PROJCS["IaRCS_04_Sioux_City-Iowa_Falls_NAD_1983_2011_LCC_US_Feet"',
            'PROJCRS["IaRCS_04_Sioux_City-Iowa_Falls_NAD_1983_2011_LCC_US_Feet"'  # GDAL 3.3+
        )
    )


def test_to_wkt__env_version():
    with Env(OSR_WKT_FORMAT="WKT2_2018"):
        assert _crs.crs_to_wkt("EPSG:4326").startswith('GEOGCRS["WGS 84",')


def test_to_wkt__invalid_version():
    with pytest.raises(CRSError):
        _crs.crs_to_wkt("EPSG:4326", wkt_version="invalid")
