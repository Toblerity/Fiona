import fiona
import pytest

from fiona import supported_drivers
from fiona.drvsupport import _driver_supports_mode
from tests.conftest import get_temp_filename


@pytest.mark.parametrize('driver', [driver for driver, raw in supported_drivers.items() if 'w' in raw and
                                    _driver_supports_mode(driver, 'w')])
def test_overwrite(tmpdir, driver, testdata_generator):
    """ Test if it is possible to overwrite a dataset """

    path = str(tmpdir.join(get_temp_filename(driver)))
    schema, crs, records1, records2, test_equal = testdata_generator(driver, range(0, 5), range(5, 10))

    # Create test file
    with fiona.open(path, 'w',
                    driver=driver,
                    crs=crs,
                    schema=schema) as c:
        c.writerecords(records1)

    # Overwrite test file
    with fiona.open(path, 'w',
                    driver=driver,
                    crs=crs,
                    schema=schema) as c:
        c.writerecords(records2)

    if driver in {'FileGDB', 'OpenFileGDB'}:
        open_driver = driver
    else:
        open_driver = None
    with fiona.open(path, driver=open_driver) as c:
        assert c.driver == driver
        items = list(c)
        assert len(items) == len(records2)
        for val_in, val_out in zip(records2, items):
            assert test_equal(driver, val_in, val_out)
