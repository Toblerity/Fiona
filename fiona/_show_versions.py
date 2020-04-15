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

    gdal_data = fiona.env.GDALDataFinder().search()
    proj_lib = fiona.env.PROJDataFinder().search()

    try:
        gdal_data_exists = os.path.exists(gdal_data)
        proj_lib_exists = os.path.exists(proj_lib)
    except:
        gdal_data_exists = "?"
        proj_lib_exists = "?"

    msg = ("Fiona version: {fiona_version}"
           "\nGDAL version: {gdal_release_name}"
           "\nPROJ version: {proj_version}"
           "\nGDAL_DATA: '{gdal_data}' Directory exists: {gdal_data_exists}"
           "\nPROJ_LIB: '{proj_lib}' Directory exists: {proj_lib_exists}"
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
                     python_exec=python_exec,
                     gdal_data=gdal_data,
                     proj_lib=proj_lib,
                     gdal_data_exists=gdal_data_exists,
                     proj_lib_exists=proj_lib_exists))
