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
# the _shim extension modules for GDAL 1.x and 2.x.
class sdist_multi_gdal(sdist):
    def run(self):
        sources = {
            "_shim1": "_shim",
            "_shim2": "_shim",
            "_shim22": "_shim",
            "_shim3": "_shim"
        }
        for src_a, src_b in sources.items():
            shutil.copy('fiona/{}.pyx'.format(src_a), 'fiona/{}.pyx'.format(src_b))
            _ = check_output(['cython', '-v', '-f', 'fiona/{}.pyx'.format(src_b),
                              '-o', 'fiona/{}.c'.format(src_a)])
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
gdalversion = None
language = None

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

    log.info("GDAL version major=%r minor=%r", gdal_major_version, gdal_minor_version)

ext_options = dict(
    include_dirs=include_dirs,
    library_dirs=library_dirs,
    libraries=libraries,
    extra_link_args=extra_link_args)

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

if source_is_repo and "clean" not in sys.argv:
    # When building from a repo, Cython is required.
    log.info("MANIFEST.in found, presume a repo, cythonizing...")
    if not cythonize:
        log.fatal("Cython.Build.cythonize not found. "
                  "Cython is required to build from a repo.")
        sys.exit(1)

    if gdalversion.startswith("1"):
        shutil.copy('fiona/_shim1.pyx', 'fiona/_shim.pyx')
        shutil.copy('fiona/_shim1.pxd', 'fiona/_shim.pxd')
    elif gdal_major_version == 2:
        if gdal_minor_version >= 2:
            log.info("Building Fiona for gdal 2.2+: {0}".format(gdalversion))
            shutil.copy('fiona/_shim22.pyx', 'fiona/_shim.pyx')
            shutil.copy('fiona/_shim22.pxd', 'fiona/_shim.pxd')
        else:
            log.info("Building Fiona for gdal 2.0.x-2.1.x: {0}".format(gdalversion))
            shutil.copy('fiona/_shim2.pyx', 'fiona/_shim.pyx')
            shutil.copy('fiona/_shim2.pxd', 'fiona/_shim.pxd')
    elif gdal_major_version == 3:
        shutil.copy('fiona/_shim3.pyx', 'fiona/_shim.pyx')
        shutil.copy('fiona/_shim3.pxd', 'fiona/_shim.pxd')

    ext_modules = cythonize([
        Extension('fiona._geometry', ['fiona/_geometry.pyx'], **ext_options),
        Extension('fiona.schema', ['fiona/schema.pyx'], **ext_options),
        Extension('fiona._transform', ['fiona/_transform.pyx'], **ext_options_cpp),
        Extension('fiona._crs', ['fiona/_crs.pyx'], **ext_options),
        Extension('fiona._env', ['fiona/_env.pyx'], **ext_options),
        Extension('fiona._err', ['fiona/_err.pyx'], **ext_options),
        Extension('fiona._shim', ['fiona/_shim.pyx'], **ext_options),
        Extension('fiona.ogrext', ['fiona/ogrext.pyx'], **ext_options)
        ],
        compiler_directives={"language_level": "3"}
    )

# If there's no manifest template, as in an sdist, we just specify .c files.
elif "clean" not in sys.argv:
    ext_modules = [
        Extension('fiona.schema', ['fiona/schema.c'], **ext_options),
        Extension('fiona._transform', ['fiona/_transform.cpp'], **ext_options_cpp),
        Extension('fiona._geometry', ['fiona/_geometry.c'], **ext_options),
        Extension('fiona._crs', ['fiona/_crs.c'], **ext_options),
        Extension('fiona._env', ['fiona/_env.c'], **ext_options),
        Extension('fiona._err', ['fiona/_err.c'], **ext_options),
        Extension('fiona.ogrext', ['fiona/ogrext.c'], **ext_options),
    ]

    if gdal_major_version == 1:
        log.info("Building Fiona for gdal 1.x: {0}".format(gdalversion))
        ext_modules.append(
            Extension('fiona._shim', ['fiona/_shim1.c'], **ext_options))
    elif gdal_major_version == 2:
        if gdal_minor_version >= 2:
            log.info("Building Fiona for gdal 2.2+: {0}".format(gdalversion))
            ext_modules.append(
                Extension('fiona._shim', ['fiona/_shim22.c'], **ext_options))
        else:
            log.info("Building Fiona for gdal 2.0.x-2.1.x: {0}".format(gdalversion))
            ext_modules.append(
                Extension('fiona._shim', ['fiona/_shim2.c'], **ext_options))
    elif gdal_major_version == 3:
        log.info("Building Fiona for gdal >= 3.0.x: {0}".format(gdalversion))
        ext_modules.append(
            Extension('fiona._shim', ['fiona/_shim3.c'], **ext_options))

requirements = [
    'attrs>=17',
    'certifi',
    'click>=4.0,<8',
    'cligj>=0.5',
    'click-plugins>=1.0',
    'six>=1.7',
    'munch',
    'argparse; python_version < "2.7"',
    'ordereddict; python_version < "2.7"',
    'enum34; python_version < "3.4"'
]

extras_require = {
    'calc': ['shapely'],
    's3': ['boto3>=1.2.4'],
    'test': ['pytest>=3', 'pytest-cov', 'boto3>=1.2.4', 'mock; python_version < "3.4"']
}

extras_require['all'] = list(set(it.chain(*extras_require.values())))


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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
        'Topic :: Scientific/Engineering :: GIS'])

if os.environ.get('PACKAGE_DATA'):
    setup_args['package_data'] = {'fiona': ['gdal_data/*', 'proj_data/*', '.libs/*', '.libs/licenses/*']}

setup(**setup_args)
