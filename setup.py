try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from distutils.core import Extension
import logging
import subprocess

logging.basicConfig()
log = logging.getLogger()

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
except Exception, e:
    log.error("Failed to get options via gdal-config: %s", str(e))

# Get text from README.txt
readme_text = file('README.rst', 'rb').read()

setup(name          = 'Fiona',
      version       = '0.7',
      description   = "Fiona is OGR's neater API",
      license       = 'BSD',
      keywords      = 'gis vector feature data',
      author        = 'Sean Gillies',
      author_email  = 'sean.gillies@gmail.com',
      maintainer        = 'Sean Gillies',
      maintainer_email  = 'sean.gillies@gmail.com',
      url   = 'http://github.com/Toblerity/Fiona',
      long_description = readme_text,
      package_dir = {'': 'src'},
      packages = ['fiona'],
      install_requires  = [],
      tests_require = ['nose'],
      ext_modules = [
        Extension(
            'fiona.ogrinit', 
            ['src/fiona/ogrinit.c'],
            include_dirs=include_dirs,
            library_dirs=library_dirs,
            libraries=libraries ),
        Extension(
            'fiona.ogrext', 
            ['src/fiona/ogrext.c'],
            include_dirs=include_dirs,
            library_dirs=library_dirs,
            libraries=libraries ),
        ],
      classifiers   = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: GIS',
        ],
)
