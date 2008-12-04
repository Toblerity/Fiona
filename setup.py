from setuptools import setup
from distutils.core import Extension
from Cython.Distutils import build_ext as build_pyx

libs = ['gdal']

# Get text from README.txt
readme_text = file('README.txt', 'rb').read()

setup(name          = 'WorldMill',
      version       = '0.1.1',
      description   = 'Access and transform geospatial feature data',
      license       = 'BSD',
      keywords      = 'gis vector feature data',
      author        = 'Sean Gillies',
      author_email  = 'sgillies@frii.com',
      maintainer        = 'Sean Gillies',
      maintainer_email  = 'sgillies@frii.com',
      url   = 'http://github.com/sgillies/worldmill/tree',
      long_description = readme_text,
      package_dir = {'': 'src'},
      packages = ['mill'],
      install_requires  = ['setuptools', 'Cython'],
      test_suite = 'tests.test_doctests.test_suite',
      ext_modules = [
        Extension('mill.workspace', ['src/mill/workspace.pyx'], libraries=libs),
        Extension(
            'mill.collection',
            ['src/mill/collection.pyx'],
            libraries=libs
            ),
        Extension('mill.ogrinit', ['src/mill/ogrinit.pyx'], libraries=libs),
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
