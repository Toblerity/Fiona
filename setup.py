from distutils.command.sdist import sdist
from distutils import log
import logging
import os
import shutil
import subprocess
import sys

from setuptools import setup
from setuptools.extension import Extension


# Use Cython if available.
try:
    from Cython.Build import cythonize
except ImportError:
    cythonize = None


def check_output(cmd):
    # since subprocess.check_output doesn't exist in 2.6
    # we wrap it here.
    try:
        out = subprocess.check_output(cmd)
        return out.decode('utf')
    except AttributeError:
        # For some reasone check_output doesn't exist
        # So fall back on Popen
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        out, err = p.communicate()
        return out


def copy_data_tree(datadir, destdir):
    try:
        shutil.rmtree(destdir)
    except OSError:
        pass
    shutil.copytree(datadir, destdir)

# Parse the version from the fiona module.
with open('fiona/__init__.py', 'r') as f:
    for line in f:
        if line.find("__version__") >= 0:
            version = line.split("=")[1].strip()
            version = version.strip('"')
            version = version.strip("'")
            break

# Fiona's auxiliary files are UTF-8 encoded and we'll specify this when
# reading with Python 3+
open_kwds = {}
if sys.version_info > (3,):
    open_kwds['encoding'] = 'utf-8'

with open('VERSION.txt', 'w', **open_kwds) as f:
    f.write(version)

with open('README.rst', **open_kwds) as f:
    readme = f.read()

with open('CREDITS.txt', **open_kwds) as f:
    credits = f.read()

with open('CHANGES.txt', **open_kwds) as f:
    changes = f.read()

# Set a flag for builds where the source directory is a repo checkout.
source_is_repo = os.path.exists("MANIFEST.in")


# Extend distutil's sdist command to generate C extension sources from
# both `ogrext`.pyx` and `ogrext2.pyx` for GDAL 1.x and 2.x.
class sdist_multi_gdal(sdist):
    def run(self):
        shutil.copy('fiona/ogrext1.pyx', 'fiona/ogrext.pyx')
        _ = check_output(['cython', '-v', '-f', 'fiona/ogrext.pyx',
                          '-o', 'fiona/ogrext1.c'])
        print(_)
        shutil.copy('fiona/ogrext2.pyx', 'fiona/ogrext.pyx')
        _ = check_output(['cython', '-v', '-f', 'fiona/ogrext.pyx',
                          '-o', 'fiona/ogrext2.c'])
        print(_)
        sdist.run(self)

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
gdalversion = '2'

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
            log.info("GDAL API version obtained from gdal-config: %s",
                     gdalversion)

    except Exception as e:
        if os.name == "nt":
            log.info("Building on Windows requires extra options to setup.py "
                     "to locate needed GDAL files.\nMore information is "
                     "available in the README.")
        else:
            log.warn("Failed to get options via gdal-config: %s", str(e))

    # Get GDAL API version from environment variable.
    if 'GDAL_VERSION' in os.environ:
        gdalversion = os.environ['GDAL_VERSION']
        log.info("GDAL API version obtained from environment: %s", gdalversion)

    # Get GDAL API version from the command line if specified there.
    if '--gdalversion' in sys.argv:
        index = sys.argv.index('--gdalversion')
        sys.argv.pop(index)
        gdalversion = sys.argv.pop(index)
        log.info("GDAL API version obtained from command line option: %s",
                 gdalversion)

    if not gdalversion:
        log.fatal("A GDAL API version must be specified. Provide a path "
                  "to gdal-config using a GDAL_CONFIG environment variable "
                  "or use a GDAL_VERSION environment variable.")
        sys.exit(1)

    if os.environ.get('PACKAGE_DATA'):
        destdir = 'fiona/gdal_data'
        if gdal_output[2]:
            log.info("Copying gdal data from %s" % gdal_output[2])
            copy_data_tree(gdal_output[2], destdir)
        else:
            # check to see if GDAL_DATA is defined
            gdal_data = os.environ.get('GDAL_DATA', None)
            if gdal_data:
                log.info("Copying gdal data from %s" % gdal_data)
                copy_data_tree(gdal_data, destdir)

        # Conditionally copy PROJ.4 data.
        projdatadir = os.environ.get('PROJ_LIB', '/usr/local/share/proj')
        if os.path.exists(projdatadir):
            log.info("Copying proj data from %s" % projdatadir)
            copy_data_tree(projdatadir, 'fiona/proj_data')

ext_options = dict(
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    libraries=libraries,
    extra_link_args=extra_link_args)

# Define the extension modules.
ext_modules = []

if source_is_repo and "clean" not in sys.argv:
    # When building from a repo, Cython is required.
    log.info("MANIFEST.in found, presume a repo, cythonizing...")
    if not cythonize:
        log.fatal("Cython.Build.cythonize not found. "
                  "Cython is required to build from a repo.")
        sys.exit(1)

    if gdalversion.startswith("1"):
        log.info("Building Fiona for gdal 1.x: {0}".format(gdalversion))
        shutil.copy('fiona/ogrext1.pyx', 'fiona/ogrext.pyx')
    else:
        log.info("Building Fiona for gdal 2.x: {0}".format(gdalversion))
        shutil.copy('fiona/ogrext2.pyx', 'fiona/ogrext.pyx')

    ext_modules = cythonize([
        Extension('fiona._geometry', ['fiona/_geometry.pyx'], **ext_options),
        Extension('fiona._transform', ['fiona/_transform.pyx'], **ext_options),
        Extension('fiona._crs', ['fiona/_crs.pyx'], **ext_options),
        Extension('fiona._drivers', ['fiona/_drivers.pyx'], **ext_options),
        Extension('fiona._err', ['fiona/_err.pyx'], **ext_options),
        Extension('fiona.ogrext', ['fiona/ogrext.pyx'], **ext_options)])

# If there's no manifest template, as in an sdist, we just specify .c files.
elif "clean" not in sys.argv:
    ext_modules = [
        Extension('fiona._transform', ['fiona/_transform.cpp'], **ext_options),
        Extension('fiona._geometry', ['fiona/_geometry.c'], **ext_options),
        Extension('fiona._crs', ['fiona/_crs.c'], **ext_options),
        Extension('fiona._drivers', ['fiona/_drivers.c'], **ext_options),
        Extension('fiona._err', ['fiona/_err.c'], **ext_options)]

    if gdalversion.startswith("1"):
        log.info("Building Fiona for gdal 1.x: {0}".format(gdalversion))
        ext_modules.append(
            Extension('fiona.ogrext', ['fiona/ogrext1.c'], **ext_options))
    else:
        log.info("Building Fiona for gdal 2.x: {0}".format(gdalversion))
        ext_modules.append(
            Extension('fiona.ogrext', ['fiona/ogrext2.c'], **ext_options))

requirements = [
    'cligj',
    'click-plugins',
    'six',
    'munch']

if sys.version_info < (2, 7):
    requirements.append('argparse')
    requirements.append('ordereddict')

if sys.version_info < (3, 4):
    requirements.append('enum34')

setup_args = dict(
    cmdclass={'sdist': sdist_multi_gdal},
    metadata_version='1.2',
    name='Fiona',
    version=version,
    requires_python='>=2.6',
    requires_external='GDAL (>=1.8)',
    description="Fiona reads and writes spatial data files",
    license='BSD',
    keywords='gis vector feature data',
    author='Sean Gillies',
    author_email='sean.gillies@gmail.com',
    maintainer='Sean Gillies',
    maintainer_email='sean.gillies@gmail.com',
    url='http://github.com/Toblerity/Fiona',
    long_description=readme + "\n" + changes + "\n" + credits,
    package_dir={'': '.'},
    packages=['fiona', 'fiona.fio'],
    entry_points='''
        [console_scripts]
        fio=fiona.fio.main:main_group

        [fiona.fio_commands]
        bounds=fiona.fio.bounds:bounds
        calc=fiona.fio.calc:calc
        cat=fiona.fio.cat:cat
        collect=fiona.fio.collect:collect
        distrib=fiona.fio.distrib:distrib
        dump=fiona.fio.dump:dump
        env=fiona.fio.env:env
        filter=fiona.fio.filter:filter
        info=fiona.fio.info:info
        insp=fiona.fio.insp:insp
        load=fiona.fio.load:load
        ls=fiona.fio.ls:ls
        ''',
    install_requires=requirements,
    extras_require={
        'calc': ['shapely'],
        'test': ['nose']},
    tests_require=['nose'],
    test_suite='nose.collector',
    ext_modules=ext_modules,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: GIS'])

if os.environ.get('PACKAGE_DATA'):
    setup_args['package_data'] = {'fiona': ['gdal_data/*', 'proj_data/*']}

setup(**setup_args)
