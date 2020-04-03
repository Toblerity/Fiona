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

        Checks if a */*gdal*/* directory is present in PATH
        and contains a gdal*.dll file.
        If none is found, GDAL_HOME is used if available.
    """

    # Parse PATH for gdal/bin
    for path in os.getenv('PATH', '').split(os.pathsep):

        if "gdal" in path.lower() and directory_contains_gdal_dll(path):
            dll_directories.append(path)

    # Use GDAL_HOME if present
    if len(dll_directories) == 0:

        gdal_home = os.getenv('GDAL_HOME', None)

        if gdal_home is not None and os.path.exists(gdal_home):

            if directory_contains_gdal_dll(gdal_home):
                dll_directories.append(gdal_home)
            elif directory_contains_gdal_dll(os.path.join(gdal_home, "bin")):
                dll_directories.append(os.path.join(gdal_home, "bin"))

        elif gdal_home is not None and not os.path.exists(gdal_home):
            log.warning("GDAL_HOME directory ({}) does not exist.".format(gdal_home))

    if len(dll_directories) == 0:
        log.warning("No dll directory found.")


if platform.system() == 'Windows' and (3, 8) <= sys.version_info:
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
