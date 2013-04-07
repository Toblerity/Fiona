try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import logging
import subprocess

from Cython.Build import cythonize
from Cython.Build.Dependencies import create_extension_list

logging.basicConfig()
log = logging.getLogger()

# Parse the version from the fiona module
for line in open('src/fiona/__init__.py', 'rb'):
    if line.find("__version__") >= 0:
        version = line.split("=")[1].strip()
        version = version.strip('"')
        version = version.strip("'")
        continue

# By default we'll try to get options via gdal-config.
# On systems without, options will need to be set in setup.cfg or on the
# setup command line.
include_dirs = []
library_dirs = []
libraries = []
try:
    gdal_config = "gdal-config"
    with open("gdal-config.txt", "w") as gcfg:
        subprocess.call([gdal_config, "--cflags"], stdout=gcfg)
        subprocess.call([gdal_config, "--libs"], stdout=gcfg)
    with open("gdal-config.txt", "r") as gcfg:
        cflags = gcfg.readline().strip()
        libs = gcfg.readline().strip()
    for item in cflags.split():
        if item.startswith("-I"):
            include_dirs.extend(item[2:].split(":"))
    for item in libs.split():
        if item.startswith("-L"):
            library_dirs.extend(item[2:].split(":"))
        elif item.startswith("-l"):
            libraries.append(item[2:])
except Exception as e:
    log.error("Failed to get options via gdal-config: %s", str(e))

# Get text from README.txt
readme_text = open('README.rst', 'rb').read()

modules = create_extension_list(['src/fiona/*.pyx'])
for module in modules:
    module.include_dirs = include_dirs
    module.library_dirs = library_dirs
    module.libraries = libraries

setup(
    name='Fiona',
    version=version,
    description="Fiona reads and writes spatial data files",
    license='BSD',
    keywords='gis vector feature data',
    author='Sean Gillies',
    author_email='sean.gillies@gmail.com',
    maintainer='Sean Gillies',
    maintainer_email='sean.gillies@gmail.com',
    url='http://github.com/Toblerity/Fiona',
    long_description=readme_text,
    package_dir={'': 'src'},
    packages=['fiona'],
    install_requires=[],
    tests_require=['nose'],
    test_suite='nose.collector',
    ext_modules=cythonize(modules),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: GIS',
    ],
)
