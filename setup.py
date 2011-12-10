from setuptools import setup
from distutils.core import Extension
from Cython.Distutils import build_ext as build_pyx

libs = ['gdal']

# Get text from README.txt
readme_text = file('README.rst', 'rb').read()

setup(name          = 'Fiona',
      version       = '0.3',
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
      tests_require = ['nose'],
      ext_modules = [
        Extension('fiona.ogrinit', ['src/fiona/ogrinit.c'], libraries=libs),
        Extension(
            'fiona.ogrext', 
            ['src/fiona/ogrext.c'], 
            libraries=libs),
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
