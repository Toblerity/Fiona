import pytest
import fiona
import fiona.drvsupport
import fiona.meta
from fiona.drvsupport import supported_drivers
from .conftest import requires_gdal2, requires_gdal23


@requires_gdal2
@pytest.mark.parametrize("driver", supported_drivers)
def test_print_driver_options(driver):
    # do not fail
    fiona.meta.print_driver_options(driver)


@requires_gdal2
@pytest.mark.parametrize("driver", supported_drivers)
def test_extension(driver):
    # do not fail
    extension = fiona.meta.extension(driver)
    print(extension, type(extension))
    assert extension is None or isinstance(extension, str)


@requires_gdal2
@pytest.mark.parametrize("driver", supported_drivers)
def test_extensions(driver):
    # do not fail
    extensions = fiona.meta.extensions(driver)
    assert extensions is None or isinstance(extensions, list)


@requires_gdal2
@pytest.mark.parametrize("driver", supported_drivers)
def test_supports_vsi(driver):
    # do not fail
    assert fiona.meta.supports_vsi(driver) in (True, False)


@requires_gdal2
@pytest.mark.parametrize("driver", supported_drivers)
def test_supported_field_types(driver):
    # do not fail
    field_types = fiona.meta.supported_field_types(driver)
    assert field_types is None or isinstance(field_types, list)


@requires_gdal23
@pytest.mark.parametrize("driver", supported_drivers)
def test_supported_sub_field_types(driver):
    # do not fail
    sub_field_types = fiona.meta.supported_sub_field_types(driver)
    assert sub_field_types is None or isinstance(sub_field_types, list)
