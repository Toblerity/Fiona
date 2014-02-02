=================================================================
Fiona: OGR's neat, nimble, no-nonsense API for Python programmers
=================================================================

**Fiona** provides uncomplicated Python interfaces to functions in OGR_,
the best open source C/C++ library for reading and writing geographic vector
data.

.. image:: https://travis-ci.org/Toblerity/Fiona.png?branch=master   
   :target: https://travis-ci.org/Toblerity/Fiona

Fiona is designed to be simple and dependable. It focuses on reading and
writing data in standard Python IO style, and relies upon familiar Python types
and protocols such as files, dictionaries, mappings, and iterators instead of
classes specific to OGR. Fiona can read and write real-world data using
multi-layered GIS formats and zipped virtual file systems and integrates
readily with other Python GIS packages such as pyproj_, Rtree_, and Shapely_.

For more details, see:

* Fiona `home page <https://github.com/Toblerity/Fiona>`__
* Fiona `docs and manual <http://toblerity.github.com/fiona/>`__
* Fiona `examples <https://github.com/Toblerity/Fiona/tree/master/examples>`__

Dependencies
============

Fiona requires Python 2.6, 2.7, or 3.3 and GDAL/OGR 1.8+. To build from
a source distribution or repository copy you will need a C compiler and GDAL
and Python development headers and libraries (libgdal1-dev for Debian/Ubuntu,
gdal-dev for CentOS/Fedora).

The popular `Kyngchaos GDAL frameworks
<http://www.kyngchaos.com/software/frameworks#gdal_complete>`__ will satisfy
the dependency for OS X. Fiona's author uses Homebrew (``brew install gdal``)
on OS X.

While there are no official binary distributions or Windows support at this
time, you can find Windows installers at
http://www.lfd.uci.edu/%7Egohlke/pythonlibs/#fiona.


Installation
============

Requirements
------------

Fiona depends on the modules ``six`` and ``argparse``. The latter is standard
in Python 2.7+. Easy_install and pip will fetch these requirements for you, but
users installing Fiona from a Windows installer must get them separately.

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

Collections
-----------

Records are read from and written to ``file``-like `Collection` objects
returned from the ``fiona.open()`` function.  Records are mappings modeled on
the GeoJSON format. They don't have any spatial methods of their own, so if you
want to do anything fancy with them you will probably need Shapely or something
like it. Here is an example of using Fiona to read some records from one data
file, change their geometry attributes, and write them to a new data file.

.. code-block:: python

    import fiona
  
    # Register format drivers with a context manager
    
    with fiona.drivers():

        # Open a file for reading. We'll call this the "source."
        
        with fiona.open('docs/data/test_uk.shp') as source:

            # The file we'll write to, the "sink", must be initialized
            # with a coordinate system, a format driver name, and
            # a record schema.  We can get initial values from the open
            # collection's ``meta`` property and then modify them as
            # desired.

            meta = source.meta
            meta['schema']['geometry'] = 'Point'

            # Open an output file, using the same format driver and
            # coordinate reference system as the source. The ``meta``
            # mapping fills in the keyword parameters of fiona.open().
            
            with fiona.open('test_write.shp', 'w', **meta) as sink:

                # Process only the records intersecting a box.
                for f in source.filter(bbox=(-5.0, 55.0, 0.0, 60.0)):
          
                    # Get a point on the boundary of the record's
                    # geometry.
                    
                    f['geometry'] = {
                        'type': 'Point',
                        'coordinates': f['geometry']['coordinates'][0][0]}
              
                    # Write the record out.
                    
                    sink.write(f)
              
        # The sink's contents are flushed to disk and the file is
        # closed when its ``with`` block ends. This effectively
        # executes ``sink.flush(); sink.close()``.

    # At the end of the ``with fiona.drivers()`` block, context
    # manager exits and all drivers are de-registered.

The fiona.drivers() function and context manager are new in 1.1. The
example above shows the way to use it to register and de-register
drivers in a deterministic and efficient way. Code written for Fiona 1.0
will continue to work: opened collections may manage the global driver
registry if no other manager is present.

Reading Multilayer data
-----------------------

Collections can also be made from single layers within multilayer files or
directories of data. The target layer is specified by name or by its integer
index within the file or directory. The ``fiona.listlayers()`` function
provides an index ordered list of layer names.

.. code-block:: python

    with fiona.drivers():

        for layername in fiona.listlayers('docs/data'):
            with fiona.open('docs/data', layer=layername) as c:
                print(layername, len(c))
    
    # Output:
    # test_uk 48

Layer can also be specified by index. In this case, ``layer=0`` and
``layer='test_uk'`` specify the same layer in the data file or directory.

.. code-block:: python

    with fiona.drivers():

        for i, layername in enumerate(fiona.listlayers('docs/data')):
            with fiona.open('docs/data', layer=i) as c:
                print(i, layername, len(c))
    
    # Output:
    # 0 test_uk 48

Writing Multilayer data
-----------------------

Multilayer data can be written as well. Layers must be specified by name when
writing.

.. code-block:: python
    
    with fiona.drivers():

        with open('docs/data/test_uk.shp') as c:
            meta = c.meta
            f = next(c)
    
        with fiona.open('/tmp/foo', 'w', layer='bar', **meta) as c:
            c.write(f)
    
        print(fiona.listlayers('/tmp/foo'))
        # Output: ['bar']
    
        with fiona.open('/tmp/foo', layer='bar') as c:
            print(len(c))
            f = next(c)
            print(f['geometry']['type'])
            print(f['properties'])
    
        # Output:
        # 1
        # Polygon
        # {'FIPS_CNTRY': 'UK', 'POP_CNTRY': 60270708.0, 'CAT': 232.0, 
        #  'AREA': 244820.0, 'CNTRY_NAME': 'United Kingdom'}

A view of the /tmp/foo directory will confirm the creation of the new files.

.. code-block:: console

    $ ls /tmp/foo
    bar.cpg bar.dbf bar.prj bar.shp bar.shx

Collections from archives and virtual file systems
--------------------------------------------------

Zip and Tar archives can be treated as virtual filesystems and Collections can
be made from paths and layers within them. In other words, Fiona lets you read
and write zipped Shapefiles.

.. code-block:: python

    with fiona.drivers():

        for i, layername in enumerate(
                fiona.listlayers(
                    '/', 
                    vfs='zip://docs/data/test_uk.zip')):
            with fiona.open(
                    '/', 
                    vfs='zip://docs/data/test_uk.zip', 
                    layer=i) as c:
                print(i, layername, len(c))
    
    # Output:
    # 0 test_uk 48

Dumpgj
======

Fiona installs a script named "dumpgj". It converts files to GeoJSON with
JSON-LD context as an option.

.. code-block:: console

  $ dumpgj --help
  usage: dumpgj [-h] [-d] [-n N] [--compact] [--encoding ENC]
                [--record-buffered] [--ignore-errors] [--use-ld-context]
                [--add-ld-context-item TERM=URI]
                infile [outfile]
  
  Serialize a file's records or description to GeoJSON
  
  positional arguments:
    infile                input file name
    outfile               output file name, defaults to stdout if omitted
  
  optional arguments:
    -h, --help            show this help message and exit
    -d, --description     serialize file's data description (schema) only
    -n N, --indent N      indentation level in N number of chars
    --compact             use compact separators (',', ':')
    --encoding ENC        Specify encoding of the input file
    --record-buffered     Economical buffering of writes at record, not
                          collection (default), level
    --ignore-errors       log errors but do not stop serialization
    --use-ld-context      add a JSON-LD context to JSON output
    --add-ld-context-item TERM=URI
                          map a term to a URI and add it to the output's JSON LD
                          context

Fiona.insp
==========

Like an ogrinfo on steroids, pass a filename to "fiona.insp".

.. code-block:: console

    $ fiona.insp docs/data/test_uk.shp
    Fiona 1.1.1 Interactive Inspector (Python 2.7.5)
    Type "src.schema", "next(src)", or "help(src)" for more information.
    >>>

Development and testing
=======================

Building from the source requires Cython. Tests require Nose. If the GDAL/OGR
libraries, headers, and `gdal-config`_ program are installed to well known
locations on your system (via your system's package manager), you can do this::

  (fiona_env)$ git clone git://github.com/Toblerity/Fiona.git
  (fiona_env)$ cd Fiona
  (fiona_env)$ python setup.py develop
  (fiona_env)$ nosetests

If you have a non-standard environment, you'll need to specify the include and
lib dirs and GDAL library on the command line::

  (fiona_env)$ python setup.py build_ext -I/path/to/gdal/include -L/path/to/gdal/lib -lgdal develop
  (fiona_env)$ nosetests

.. _OGR: http://www.gdal.org/ogr
.. _pyproj: http://pypi.python.org/pypi/pyproj/
.. _Rtree: http://pypi.python.org/pypi/Rtree/
.. _Shapely: http://pypi.python.org/pypi/Shapely/
.. _gdal-config: http://www.gdal.org/gdal-config.html

