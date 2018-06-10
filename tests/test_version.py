import fiona
from fiona.ogrext import GDALVersion

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
