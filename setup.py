# Fiona build script.

import logging
import os
import shutil
import subprocess
import sys

from setuptools import setup
from setuptools.extension import Extension


# Ensure minimum version of Python is running
if sys.version_info[0:2] < (3, 6):
    raise RuntimeError('Fiona requires Python>=3.6')

# Use Cython if available.
try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None


def check_output(cmd):
    return subprocess.check_output(cmd).decode('utf')


def copy_data_tree(datadir, destdir):
    try:
        shutil.rmtree(destdir)
    except OSError:
        pass
    shutil.copytree(datadir, destdir)


# Building Fiona requires options that can be obtained from GDAL's gdal-config
# program or can be specified using setup arguments. The latter override the
# former.
#
# A GDAL API version is strictly required. Without this the setup script
# cannot know whether to use the GDAL version 1 or 2 source files. The GDAL
# API version can be specified in 2 ways.
#
# 1. By the gdal-config program, optionally pointed to by GDAL_CONFIG
# 2. By a GDAL_VERSION environment variable. This overrides number 1.


include_dirs = []
library_dirs = []
libraries = []
extra_link_args = []
gdal_output = [None for i in range(4)]
gdalversion = None
language = None
gdal_major_version = 0
gdal_minor_version = 0

if 'clean' not in sys.argv:
    try:
        gdal_config = os.environ.get('GDAL_CONFIG', 'gdal-config')
        for i, flag in enumerate(
                ["--cflags", "--libs", "--datadir", "--version"]):
            gdal_output[i] = check_output([gdal_config, flag]).strip()
        for item in gdal_output[0].split():
            if item.startswith("-I"):
                include_dirs.extend(item[2:].split(":"))
        for item in gdal_output[1].split():
            if item.startswith("-L"):
                library_dirs.extend(item[2:].split(":"))
            elif item.startswith("-l"):
                libraries.append(item[2:])
            else:
                # e.g. -framework GDAL
                extra_link_args.append(item)
        gdalversion = gdal_output[3]
        if gdalversion:
            logging.info("GDAL API version obtained from gdal-config: %s",
                         gdalversion)

    except Exception as e:
        if os.name == "nt":
            logging.info("Building on Windows requires extra options to"
                         " setup.py to locate needed GDAL files.\nMore"
                         " information is available in the README.")
        else:
            logging.warn("Failed to get options via gdal-config: %s", str(e))

    # Get GDAL API version from environment variable.
    if 'GDAL_VERSION' in os.environ:
        gdalversion = os.environ['GDAL_VERSION']
        logging.info("GDAL API version obtained from environment: %s",
                     gdalversion)

    # Get GDAL API version from the command line if specified there.
    if '--gdalversion' in sys.argv:
        index = sys.argv.index('--gdalversion')
        sys.argv.pop(index)
        gdalversion = sys.argv.pop(index)
        logging.info("GDAL API version obtained from command line option: %s",
                     gdalversion)

    if not gdalversion:
        logging.fatal("A GDAL API version must be specified. Provide a path "
                      "to gdal-config using a GDAL_CONFIG environment "
                      "variable or use a GDAL_VERSION environment variable.")
        sys.exit(1)

    if os.environ.get('PACKAGE_DATA'):
        destdir = 'fiona/gdal_data'
        if gdal_output[2]:
            logging.info("Copying gdal data from %s" % gdal_output[2])
            copy_data_tree(gdal_output[2], destdir)
        else:
            # check to see if GDAL_DATA is defined
            gdal_data = os.environ.get('GDAL_DATA', None)
            if gdal_data:
                logging.info("Copying gdal data from %s" % gdal_data)
                copy_data_tree(gdal_data, destdir)

        # Conditionally copy PROJ DATA.
        projdatadir = os.environ.get('PROJ_DATA', os.environ.get('PROJ_LIB', '/usr/local/share/proj'))
        if os.path.exists(projdatadir):
            logging.info("Copying proj data from %s" % projdatadir)
            copy_data_tree(projdatadir, 'fiona/proj_data')

    if "--cython-language" in sys.argv:
        index = sys.argv.index("--cython-language")
        sys.argv.pop(index)
        language = sys.argv.pop(index).lower()

    gdal_version_parts = gdalversion.split('.')
    gdal_major_version = int(gdal_version_parts[0])
    gdal_minor_version = int(gdal_version_parts[1])

    if (gdal_major_version, gdal_minor_version) < (3, 1):
        raise SystemExit(
            "ERROR: GDAL >= 3.1 is required for fiona. "
            "Please upgrade GDAL."
        )

    logging.info("GDAL version major=%r minor=%r", gdal_major_version,
                 gdal_minor_version)

compile_time_env = {
    "CTE_GDAL_MAJOR_VERSION": gdal_major_version,
    "CTE_GDAL_MINOR_VERSION": gdal_minor_version,
}

ext_options = dict(
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    libraries=libraries,
    extra_link_args=extra_link_args,
    cython_compile_time_env=compile_time_env,
)

# Enable coverage for cython pyx files.
if os.environ.get('CYTHON_COVERAGE'):
    from Cython.Compiler.Options import get_directive_defaults
    directive_defaults = get_directive_defaults()
    directive_defaults['linetrace'] = True
    directive_defaults['binding'] = True

    ext_options.update(dict(
        define_macros=[("CYTHON_TRACE_NOGIL", "1")]))

# GDAL 2.3+ requires C++11

if language == "c++":
    ext_options["language"] = "c++"
    if sys.platform != "win32":
        ext_options["extra_compile_args"] = ["-std=c++11"]

ext_options_cpp = ext_options.copy()
if sys.platform != "win32":
    ext_options_cpp["extra_compile_args"] = ["-std=c++11"]


# Define the extension modules.
ext_modules = []

if "clean" not in sys.argv:
    # When building from a repo, Cython is required.
    logging.info("MANIFEST.in found, presume a repo, cythonizing...")
    if not cythonize:
        raise SystemExit(
            "Cython.Build.cythonize not found. "
            "Cython is required to build fiona."
        )

    ext_modules = cythonize(
        [
            Extension("fiona._geometry", ["fiona/_geometry.pyx"], **ext_options),
            Extension("fiona.schema", ["fiona/schema.pyx"], **ext_options),
            Extension("fiona._transform", ["fiona/_transform.pyx"], **ext_options_cpp),
            Extension("fiona.crs", ["fiona/crs.pyx"], **ext_options),
            Extension("fiona._env", ["fiona/_env.pyx"], **ext_options),
            Extension("fiona._err", ["fiona/_err.pyx"], **ext_options),
            Extension("fiona.ogrext", ["fiona/ogrext.pyx"], **ext_options),
        ],
        compiler_directives={"language_level": "3"},
        compile_time_env=compile_time_env,
    )

# Include these files for binary wheels
fiona_package_data = ['gdal.pxi', '*.pxd']

if os.environ.get('PACKAGE_DATA'):
    fiona_package_data.extend([
        'gdal_data/*',
        'proj_data/*',
        '.libs/*',
        '.libs/licenses/*',
    ])

# See pyproject.toml for project metadata
setup(
    name="Fiona",  # need by GitHub dependency graph
    package_data={"fiona": fiona_package_data},
    ext_modules=ext_modules,
)
