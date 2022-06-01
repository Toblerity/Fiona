from distutils.command.sdist import sdist
from distutils import log
import itertools as it
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
    return subprocess.check_output(cmd).decode('utf')

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
            version = line.split("=")[1].strip().strip('"').strip("'")
            break

# Fiona's auxiliary files are UTF-8 encoded
open_kwds = {'encoding': 'utf-8'}

with open('VERSION.txt', 'w', **open_kwds) as f:
    f.write(version)

with open('README.rst', **open_kwds) as f:
    readme = f.read()

with open('CREDITS.txt', **open_kwds) as f:
    credits = f.read()

with open('CHANGES.txt', **open_kwds) as f:
    changes = f.read()

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

    log.info("GDAL version major=%r minor=%r", gdal_major_version, gdal_minor_version)

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
    log.info("MANIFEST.in found, presume a repo, cythonizing...")
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

requirements = [
    'attrs>=17',
    'certifi',
    'click>=4.0',
    'cligj>=0.5',
    'click-plugins>=1.0',
    'munch',
    "setuptools",
]

extras_require = {
    'calc': ['shapely'],
    's3': ['boto3>=1.2.4'],
    'test': ['pytest>=3', 'pytest-cov', 'boto3>=1.2.4']
}

extras_require['all'] = list(set(it.chain(*extras_require.values())))


setup_args = dict(
    metadata_version='1.2',
    name='Fiona',
    version=version,
    python_requires='>=3.7',
    requires_external='GDAL (>=3.1)',
    description="Fiona reads and writes spatial data files",
    license='BSD',
    keywords='gis vector feature data',
    author='Sean Gillies',
    author_email='sean.gillies@gmail.com',
    maintainer='Sean Gillies',
    maintainer_email='sean.gillies@gmail.com',
    url='https://github.com/Toblerity/Fiona',
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
        rm=fiona.fio.rm:rm
        ''',
    install_requires=requirements,
    extras_require=extras_require,
    ext_modules=ext_modules,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Topic :: Scientific/Engineering :: GIS'])

if os.environ.get('PACKAGE_DATA'):
    setup_args['package_data'] = {'fiona': ['gdal_data/*', 'proj_data/*', '.libs/*', '.libs/licenses/*']}

setup(**setup_args)
