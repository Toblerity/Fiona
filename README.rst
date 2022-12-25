=====
Fiona
=====

Fiona streams simple feature data to and from GIS formats like GeoPackage and
Shapefile. This project includes Python modules and a CLI.

.. image:: https://github.com/Toblerity/Fiona/workflows/Linux%20CI/badge.svg?branch=maint-1.9
   :target: https://github.com/Toblerity/Fiona/actions?query=branch%3Amaint-1.9

.. image:: https://ci.appveyor.com/api/projects/status/github/Toblerity/Fiona?svg=true
   :target: https://ci.appveyor.com/project/sgillies/fiona/branch/maint-1.9

.. image:: https://coveralls.io/repos/Toblerity/Fiona/badge.svg
   :target: https://coveralls.io/r/Toblerity/Fiona

Fiona depends on `GDAL <https://gdal.org>`__ but is different from GDAL's own
`bindings <https://gdal.org/api/python_bindings.html>`__. Fiona is designed to
be highly productive and easy to read, like Python itself. Its goal is to help
developers write entirely new kinds of GIS systems which read and run like
Python programs. 

Fiona can read and write real-world data using multi-layered GIS formats,
zipped and in-memory virtual file systems, from files on your hard drive or in
cloud storage.

For more details, please see:

* Fiona `home page <https://github.com/Toblerity/Fiona>`__
* `Docs and manual <https://fiona.readthedocs.io/>`__
* `Examples <https://github.com/Toblerity/Fiona/tree/master/examples>`__
* Main `user discussion group <https://fiona.groups.io/g/main>`__
* `Developers discussion group <https://fiona.groups.io/g/dev>`__

Installation
============

Fiona has several `extension modules
<https://docs.python.org/3/extending/extending.html>`__ which link against
libgdal. This complicates installation. Binary distributions (wheels)
containing libgdal and its own dependencies are available from the Python
Package Index and can be installed using `pip`.

.. code-block:: console

    pip install fiona

These wheels are mainly intended to make installation easy for simple
applications, not so much for production. They are not tested for compatibility
with all other binary wheels, conda packages, or QGIS, and omit many of GDAL's
optional format drivers. If you need, for example, GML support you will need to
build and install Fiona from a source distribution.

Many users find Anaconda and conda-forge a good way to install Fiona.

Fiona 1.9 (coming soon) requires Python 3.7 or higher and GDAL 3.2 or higher.

Usage
=====

Collections
-----------

Features are read from and written to ``file``-like ``Collection`` objects
returned from the ``fiona.open()`` function. Features are data classes modeled on
the GeoJSON format. They don't have any spatial methods of their own, so if you
want to do anything fancy with them you will need Shapely or something
like it. Here is an example of using Fiona to read some features from one data
file, change their geometry attributes, and write them to a new data file.

.. code-block:: python

    import fiona

    # Open a file for reading. We'll call this the source.

    with fiona.open("tests/data/coutwildrnp.shp") as src:

        # The file we'll write to must be initialized with a coordinate
        # system, a format driver name, and a record schema. We can get
        # initial values from the open source's meta property and then
        # modify them as we need.

        meta = src.meta
        meta["schema"]["geometry"] = "Point"

        # Open an output file, using the same format driver and
        # coordinate reference system as the source. The meta
        # mapping fills in the keyword parameters of fiona.open.

        with fiona.open("test_write.shp", "w", **meta) as dst:

            # Process only the records intersecting a box.
            for f in src.filter(bbox=(-107.0, 37.0, -105.0, 39.0)):

                # Get a point on the boundary of the record's
                # geometry.

                new_geom = fiona.Geometry(
                    type="Point", coordinates=f.geometry.coordinates[0][0]
                )

                # Write the feature out.

                dst.write(
                    fiona.Feature(
                        geometry=new_geom, properties=Properties.from_dict(**f.properties)
                    )
                )

    # The destination's contents are flushed to disk and the file is
    # closed when its with block ends. This effectively
    # executes ``dst.flush(); dst.close()``.

CLI
===

Fiona's command line interface, named "fio", is documented at `docs/cli.rst
<https://github.com/Toblerity/Fiona/blob/master/docs/cli.rst>`__. Its ``fio
cat`` command streams GeoJSON features from any dataset.

.. code-block:: console

    $ fio cat --compact tests/data/coutwildrnp.shp | jq -c '.'
    {"geometry":{"coordinates":[[[-111.73527526855469,41.995094299316406],...]]}}
    ...
