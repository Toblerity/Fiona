import fiona
from fiona.ogrext import GDALVersion
import platform
import re
import os
from tests.conftest import travis_only


def test_version_tuple():
    version = fiona.gdal_version
    assert version.major >= 1 and isinstance(version.major, int)
    assert version.minor >= 0 and isinstance(version.minor, int)
    assert version.revision >= 0 and isinstance(version.revision, int)


def test_version_comparison():
    # version against version
    assert GDALVersion(4, 0, 0) > GDALVersion(3, 2, 1)
    assert GDALVersion(2, 0, 0) < GDALVersion(3, 2, 1)
    assert GDALVersion(3, 2, 2) > GDALVersion(3, 2, 1)
    assert GDALVersion(3, 2, 0) < GDALVersion(3, 2, 1)
    
    # tuple against version
    assert (4, 0, 0) > GDALVersion(3, 2, 1)
    assert (2, 0, 0) < GDALVersion(3, 2, 1)
    assert (3, 2, 2) > GDALVersion(3, 2, 1)
    assert (3, 2, 0) < GDALVersion(3, 2, 1)


@travis_only
def test_debug_information(capsys):

    version_pattern = re.compile(r"(\d+).(\d+).(\d+)")

    os_info = "{system} {release}".format(system=platform.system(),
                                          release=platform.release())
    python_version = platform.python_version()

    msg = ("Fiona version: {fiona_version}"
           "\nGDAL version: {gdal_release_name}"
           "\nPROJ version: {proj_version}"
           "\n"
           "\nOS: {os_info}"
           "\nPython: {python_version}")

    if fiona.gdal_version < GDALVersion(3, 0, 1):
        proj_version = "Proj version not available"
    else:
        proj_version = os.getenv("PROJVERSION")
        proj_version = re.match(version_pattern, proj_version).group(0)

    gdal_version = os.getenv("GDALVERSION")
    gdal_version = re.match(version_pattern, gdal_version).group(0)

    msg_formatted = msg.format(fiona_version=fiona.__version__,
                               gdal_release_name=gdal_version,
                               proj_version=proj_version,
                               os_info=os_info,
                               python_version=python_version)

    fiona.print_debug_information()
    captured = capsys.readouterr()

    assert captured.out.strip() == msg_formatted.strip()
