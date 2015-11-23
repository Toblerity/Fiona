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

logging.basicConfig()
log = logging.getLogger()

# python -W all setup.py ...
if 'all' in sys.warnoptions:
    log.level = logging.DEBUG

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
            continue

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


def copy_gdalapi(gdalversion):
    if gdalversion[0] == u'1':
        log.info("Building Fiona for gdal 1.x: {}".format(gdalversion))
        shutil.copy('fiona/ogrext1.pyx', 'fiona/ogrext.pyx')
        shutil.copy('fiona/ograpi1.pxd', 'fiona/ograpi.pxd')
    else:
        log.info("Building Fiona for gdal 2.x: {}".format(gdalversion))
        shutil.copy('fiona/ogrext2.pyx', 'fiona/ogrext.pyx')
        shutil.copy('fiona/ograpi2.pxd', 'fiona/ograpi.pxd')

if '--gdalversion' in sys.argv:
    index = sys.argv.index('--gdalversion')
    sys.argv.pop(index)
    gdalversion = sys.argv.pop(index)
    copy_gdalapi(gdalversion)

# By default we'll try to get options via gdal-config. On systems without,
# options will need to be set in setup.cfg or on the setup command line.
include_dirs = []
library_dirs = []
libraries = []
extra_link_args = []
gdal_output = [None] * 4

try:
    gdal_config = os.environ.get('GDAL_CONFIG', 'gdal-config')
    for i, flag in enumerate(("--cflags", "--libs", "--datadir", "--version")):
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

    copy_gdalapi(gdal_output[3])

except Exception as e:
    if os.name == "nt":
        log.info(("Building on Windows requires extra options to setup.py to locate needed GDAL files.\n"
                   "More information is available in the README."))
    else:
        log.warning("Failed to get options via gdal-config: %s", str(e))

    # Conditionally copy the GDAL data. To be used in conjunction with
    # the bdist_wheel command to make self-contained binary wheels.
    if os.environ.get('PACKAGE_DATA'):
        try:
            shutil.rmtree('fiona/gdal_data')
        except OSError:
            pass
        shutil.copytree(datadir, 'fiona/gdal_data')
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

# When building from a repo, Cython is required.
if os.path.exists("MANIFEST.in") and "clean" not in sys.argv:
    log.info("MANIFEST.in found, presume a repo, cythonizing...")
    if not cythonize:
        log.critical(
            "Cython.Build.cythonize not found. "
            "Cython is required to build from a repo.")
        sys.exit(1)

    ext_modules = cythonize([
        Extension('fiona._geometry', ['fiona/_geometry.pyx'], **ext_options),
        Extension('fiona._transform', ['fiona/_transform.pyx'], **ext_options),
        Extension('fiona._drivers', ['fiona/_drivers.pyx'], **ext_options),
        Extension('fiona._err', ['fiona/_err.pyx'], **ext_options),
        Extension('fiona.ogrext', ['fiona/ogrext.pyx'], **ext_options)])
# If there's no manifest template, as in an sdist, we just specify .c files.
else:
    ext_modules = [
        Extension('fiona._transform', ['fiona/_transform.cpp'], **ext_options),
        Extension('fiona._geometry', ['fiona/_geometry.c'], **ext_options),
        Extension('fiona._drivers', ['fiona/_drivers.c'], **ext_options),
        Extension('fiona._err', ['fiona/_err.c'], **ext_options),
        Extension('fiona.ogrext', ['fiona/ogrext.c'], **ext_options)]

requirements = [
    'cligj',
    'click-plugins',
    'six',
    'munch'
]
if sys.version_info < (2, 7):
    requirements.append('argparse')
    requirements.append('ordereddict')

setup_args = dict(
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
        cat=fiona.fio.cat:cat
        collect=fiona.fio.cat:collect
        distrib=fiona.fio.cat:distrib
        dump=fiona.fio.cat:dump
        env=fiona.fio.info:env
        info=fiona.fio.info:info
        insp=fiona.fio.info:insp
        load=fiona.fio.cat:load
        filter=fiona.fio.filter:filter
        ''',
    install_requires=requirements,
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
        'Topic :: Scientific/Engineering :: GIS',
    ])

if os.environ.get('PACKAGE_DATA'):
    setup_args['package_data'] = {'fiona': ['gdal_data/*', 'proj_data/*']}

setup(**setup_args)
