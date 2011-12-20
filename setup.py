try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from distutils.core import Extension

libs = ['gdal']

# Get text from README.txt
readme_text = file('README.rst', 'rb').read()

setup(name          = 'Fiona',
      version       = '0.5',
      description   = "Fiona is OGR's neater API",
      license       = 'BSD',
      keywords      = 'gis vector feature data',
      author        = 'Sean Gillies',
      author_email  = 'sgillies@frii.com',
      maintainer        = 'Sean Gillies',
      maintainer_email  = 'sgillies@frii.com',
      url   = 'http://github.com/sgillies/fiona',
      long_description = readme_text,
      package_dir = {'': 'src'},
      packages = ['fiona'],
      install_requires  = [], #'setuptools', 'Cython'],
      tests_require = ['nose'],
      ext_modules = [
        Extension('fiona.ogrinit', ['src/fiona/ogrinit.c'], libraries=libs),
        Extension(
            'fiona.ogrext', 
            ['src/fiona/ogrext.c'], 
            libraries=libs),
        ],
      classifiers   = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: GIS',
        ],
)
