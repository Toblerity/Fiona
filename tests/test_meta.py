import pytest
import fiona
import fiona.drvsupport
import fiona.meta
from fiona.drvsupport import supported_drivers
from .conftest import requires_gdal2


@requires_gdal2
@pytest.mark.parametrize("driver", supported_drivers)
def test_print_driver_options(driver):
    # do not fail
    fiona.meta.print_driver_options(driver)


@requires_gdal2
@pytest.mark.parametrize("driver", supported_drivers)
def test_extensions(driver):
    # do not fail
    isinstance(fiona.meta.extensions(driver), list)


@requires_gdal2
@pytest.mark.parametrize("driver", supported_drivers)
def test_supports_vsi(driver):
    # do not fail
    assert fiona.meta.supports_vsi(driver) in (True, False)


@requires_gdal2
@pytest.mark.parametrize("driver", supported_drivers)
def test_supported_field_types(driver):
    # do not fail
    isinstance(fiona.meta.extensions(driver), list)
