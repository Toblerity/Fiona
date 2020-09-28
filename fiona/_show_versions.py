import platform
import sys
import os
import fiona
from fiona._env import get_gdal_release_name, get_proj_version_tuple


def show_versions():
    """
    Prints information useful for bug reports
    """

    fiona_version = fiona.__version__
    gdal_release_name = get_gdal_release_name()
    proj_version_tuple = get_proj_version_tuple()
    if proj_version_tuple is not None:
        proj_version = ".".join(map(str, proj_version_tuple))
    else:
        proj_version = "Proj version not available"
    os_info = "{system} {release}".format(system=platform.system(),
                                          release=platform.release())
    python_version = platform.python_version()
    python_exec = sys.executable

    msg = ("Fiona version: {fiona_version}"
           "\nGDAL version: {gdal_release_name}"
           "\nPROJ version: {proj_version}"
           "\n"
           "\nOS: {os_info}"
           "\nPython: {python_version}"
           "\nPython executable: '{python_exec}'"
           "\n"
           )

    print(msg.format(fiona_version=fiona_version,
                     gdal_release_name=gdal_release_name,
                     proj_version=proj_version,
                     os_info=os_info,
                     python_version=python_version,
                     python_exec=python_exec))
