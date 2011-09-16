from setuptools import setup
from distutils.core import Extension
from Cython.Distutils import build_ext as build_pyx

libs = ['gdal']

# Get text from README.txt
readme_text = file('README.rst', 'rb').read()

setup(name          = 'Fiona',
      version       = '0.2',
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
      install_requires  = ['setuptools', 'Cython'],
      test_suite = 'tests.test_doctests.test_suite',
      ext_modules = [
        Extension('fiona.workspace', ['src/fiona/workspace.pyx'], libraries=libs),
        Extension(
            'fiona.collection',
            ['src/fiona/collection.pyx'],
            libraries=libs
            ),
        Extension('fiona.ogrinit', ['src/fiona/ogrinit.pyx'], libraries=libs),
        ],
      cmdclass = {'build_ext': build_pyx},
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
