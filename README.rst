======
README
======

Fiona is OGR's neater API – sleek and elegant on the outside, indomitable power
on the inside.

Fiona provides a minimal, uncomplicated Python interface to the open source GIS
community's most trusted geodata access library and integrates readily with
other Python GIS packages such as pyproj_, Rtree_, and Shapely_.

How minimal? Fiona can read features as mappings from shapefiles or other GIS
vector formats and write mappings as features to files using the same formats.
That's all. There aren't any feature or geometry classes. Features and their
geometries are just data.

Dependencies
============

Fiona requires Python 2.6+ and libgdal 1.3.2+. To build from a source
distribution or repository clone you will need a C compiler and GDAL and Python
development headers and libraries. There are no binary distributions or Windows
support at this time.

Installation
============

Assuming you're using a virtualenv (if not, skip to the 4th command) and
GDAL/OGR libraries, headers, and `gdal-config`_ program are installed to well
known locations on your system (via your system's package manager),
installation is this simple::

  $ mkdir fiona_env
  $ virtualenv fiona_env
  $ source fiona_env/bin/activate
  (fiona_env)$ pip install Fiona

If gdal-config is not available or if GDAL/OGR headers and libs aren't
installed to a well known location, you must set include dirs, library dirs,
and libraries options via the setup.cfg file or setup command line as shown
below (using ``git``)::

  (fiona_env)$ git clone git://github.com/Toblerity/Fiona.git
  (fiona_env)$ cd Fiona
  (fiona_env)$ python setup.py build_ext -I/path/to/gdal/include -L/path/to/gdal/lib -lgdal install

Usage
=====

Collections are much like ``file`` objects. Features are mappings modeled on
the GeoJSON format and if you want to do anything fancy with them you will
probably need Shapely or something like it::

  from fiona import collection

  # Open a source of features
  with collection("docs/data/test_uk.shp", "r") as source:
  
      # Define a schema for the feature sink
      schema = source.schema.copy()
      schema['geometry'] = 'Point'
      
      # Open a new sink for features
      with collection(
              "test_write.shp", "w",
              driver=source.driver, schema=schema, crs=source.crs
              ) as sink:
          
          # Process only the features intersecting a box
          for f in source.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
          
              # Get point on the boundary of the feature
              f['geometry'] = f['geometry'] = {
                  'type': 'Point',
                  'coordinates': f['geometry']['coordinates'][0][0] }
              
              # Stage feature for writing
              sink.write(f)
              
      # The sink shapefile is written to disk when its ``with`` block ends

Development and testing
=======================

Building from the source requires Cython. Tests require Nose. If the GDAL/OGR
libraries, headers, and `gdal-config`_ program are installed to well known
locations on your system (via your system's package manager), you can do this::

  (fiona_env)$ git clone git://github.com/Toblerity/Fiona.git
  (fiona_env)$ cd Fiona
  (fiona_env)$ ./cypsrc
  (fiona_env)$ python setup.py develop
  (fiona_env)$ python setup.py nosetests

If you have a non-standard environment, you'll need to specify the include and
lib dirs and GDAL library on the command line::

  (fiona_env)$ python setup.py build_ext -I/path/to/gdal/include -L/path/to/gdal/lib -lgdal develop
  (fiona_env)$ python setup.py nosetests

Credits
=======

Fiona is written by:

* Sean Gillies (https://github.com/sgillies)

With contributions by:

* Frédéric Junod (https://github.com/fredj)
* Ariel Núñez (https://github.com/ingenieroariel)
* Michael Weisman (https://github.com/mweisman)

Fiona would not be possible without the great work of Frank Warmerdam and other
GDAL/OGR developers.

Some portions of this work were supported by a grant (for Pleiades_) from the
U.S. National Endowment for the Humanities (http://www.neh.gov).

.. _libgdal: http://www.gdal.org
.. _pyproj: http://pypi.python.org/pypi/pyproj/
.. _Rtree: http://pypi.python.org/pypi/Rtree/
.. _Shapely: http://pypi.python.org/pypi/Shapely/
.. _gdal-config: http://www.gdal.org/gdal-config.html
.. _Pleiades: http://pleiades.stoa.org

