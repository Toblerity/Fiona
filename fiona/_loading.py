import glob
import os
import logging
import contextlib
import platform
import sys

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

# With Python >= 3.8 on Windows directories in PATH are not automatically
# searched for DLL dependencies and must be added manually with
# os.add_dll_directory.
# see https://github.com/Toblerity/Fiona/issues/851

dll_directories = []


def directory_contains_gdal_dll(path):
    """ Checks if a directory contains a gdal dll """
    return len(glob.glob(os.path.join(path, "gdal*.dll"))) > 0


def search_gdal_dll_directories():
    """ Search for gdal dlls

        Finds directories in PATH containing gdal.dll.
    """

    # Parse PATH for gdal/bin
    for path in os.getenv('PATH', '').split(os.pathsep):

        if directory_contains_gdal_dll(path):
            dll_directories.append(path)

    if len(dll_directories) == 0:
        log.warning("No dll directories found.")


if platform.system() == 'Windows' and sys.version_info >= (3, 8):

    # if loading of extension modules fails, search for gdal dll directories
    try:
        import fiona.ogrext
    except ImportError as e:
        search_gdal_dll_directories()


@contextlib.contextmanager
def add_gdal_dll_directories():

    dll_dirs = []
    for dll_directory in dll_directories:
        dll_dirs.append(os.add_dll_directory(dll_directory))
    try:
        yield None
    finally:
        for dll_dir in dll_dirs:
            dll_dir.close()
