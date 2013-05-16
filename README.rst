=====
Fiona
=====

Fiona is OGR's neat, nimble, no-nonsense API.

Fiona provides a minimal, uncomplicated Python interface to the open source GIS
community's most trusted geodata access library and integrates readily with
other Python GIS packages such as pyproj_, Rtree_, and Shapely_.

How minimal? Fiona can read feature records as mappings from shapefiles or
other GIS vector formats and write mappings as records to files using the same
formats. That's all. There aren't any feature or geometry classes. Records and
their geometries are just data.

For more details, see:

* Fiona `home page <https://github.com/Toblerity/Fiona>`__
* Fiona `docs and manual <http://toblerity.github.com/fiona/>`__
* Fiona `examples <https://github.com/Toblerity/Fiona/tree/master/examples>`__

Dependencies
============

Fiona requires Python 2.6+ and GDAL 1.8+. To build from a source distribution
or repository clone you will need a C compiler and GDAL and Python development
headers and libraries. While there are no official binary distributions or
Windows support at this time, you can find Windows installers at
http://www.lfd.uci.edu/%7Egohlke/pythonlibs/#fiona.

Installation
============

Unix-like systems
-----------------

Assuming you're using a virtualenv (if not, skip to the 4th command) and
GDAL/OGR libraries, headers, and `gdal-config`_ program are installed to well
known locations on your system via your system's package manager (``brew
install gdal`` using Homebrew on OS X), installation is this simple::

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

Windows
-------

Binary installers are available at
http://www.lfd.uci.edu/~gohlke/pythonlibs/#fiona and coming eventually to PyPI.

Usage
=====

Records are read from and written to ``file``-like `Collection` objects.
Records are mappings modeled on the GeoJSON format. They don't have any spatial
methods of their own, so if you want to do anything fancy with them you will
probably need Shapely or something like it. Here is an example of using Fiona
to read some records from one data file, change their geometry attributes, and
write them to a new data file.

::

  import fiona

  # Open a file for reading. We'll call this the "source."
  with fiona.open('docs/data/test_uk.shp', 'r') as source:
  
      # The file we'll write to, the "sink", must be initialized with a
      # coordinate system, a format driver name, and a record schema.
      sink_schema = source.schema.copy()
      sink_schema['geometry'] = 'Point'
      
      # Open an output file, using the same format driver and coordinate
      # reference system as the source.
      with fiona.open(
              'test_write.shp', 'w',
              crs=source.crs, driver=source.driver, schema=sink_schema,
              ) as sink:
          
          # Process only the records intersecting a box.
          for f in source.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
          
              # Get a point on the boundary of the record's geometry.
              f['geometry'] = {
                  'type': 'Point',
                  'coordinates': f['geometry']['coordinates'][0][0]}
              
              # Write the record out.
              sink.write(f)
              
      # The sink's contents are flushed to disk and the file is closed
      # when its ``with`` block ends. This effectively executes 
      # ``sink.flush(); sink.close()``.

Development and testing
=======================

Building from the source requires Cython. Tests require Nose. If the GDAL/OGR
libraries, headers, and `gdal-config`_ program are installed to well known
locations on your system (via your system's package manager), you can do this::

  (fiona_env)$ git clone git://github.com/Toblerity/Fiona.git
  (fiona_env)$ cd Fiona
  (fiona_env)$ python setup.py build_ext --inplace
  (fiona_env)$ python setup.py develop
  (fiona_env)$ python setup.py nosetests

If you have a non-standard environment, you'll need to specify the include and
lib dirs and GDAL library on the command line::

  (fiona_env)$ python setup.py build_ext -I/path/to/gdal/include -L/path/to/gdal/lib -lgdal develop
  (fiona_env)$ python setup.py nosetests

.. _libgdal: http://www.gdal.org
.. _pyproj: http://pypi.python.org/pypi/pyproj/
.. _Rtree: http://pypi.python.org/pypi/Rtree/
.. _Shapely: http://pypi.python.org/pypi/Shapely/
.. _gdal-config: http://www.gdal.org/gdal-config.html

