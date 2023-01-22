=====
Fiona
=====

.. image:: https://github.com/Toblerity/Fiona/workflows/Linux%20CI/badge.svg?branch=maint-1.9
   :target: https://github.com/Toblerity/Fiona/actions?query=branch%3Amaint-1.9

Fiona streams simple feature data to and from GIS formats like GeoPackage and
Shapefile.

Fiona can read and write real-world data using multi-layered GIS formats,
zipped and in-memory virtual file systems, from files on your hard drive or in
cloud storage. This project includes Python modules and a command line
interface (CLI).

Fiona depends on `GDAL <https://gdal.org>`__ but is different from GDAL's own
`bindings <https://gdal.org/api/python_bindings.html>`__. Fiona is designed to
be highly productive and to make it easy to write code which is easy to read.

Installation
============

Fiona has several `extension modules
<https://docs.python.org/3/extending/extending.html>`__ which link against
libgdal. This complicates installation. Binary distributions (wheels)
containing libgdal and its own dependencies are available from the Python
Package Index and can be installed using pip.

.. code-block:: console

    pip install fiona

These wheels are mainly intended to make installation easy for simple
applications, not so much for production. They are not tested for compatibility
with all other binary wheels, conda packages, or QGIS, and omit many of GDAL's
optional format drivers. If you need, for example, GML support you will need to
build and install Fiona from a source distribution.

Many users find Anaconda and conda-forge a good way to install Fiona and get
access to more optional format drivers (like GML).

Fiona 1.9 (coming soon) requires Python 3.7 or higher and GDAL 3.2 or higher.

Python Usage
============

Features are read from and written to file-like ``Collection`` objects
returned from the ``fiona.open()`` function. Features are data classes modeled
on the GeoJSON format. They don't have any spatial methods of their own, so if
you want to do anything fancy with them you will need Shapely or something like
it. Here is an example of using Fiona to read some features from one data file,
change their geometry attributes using Shapely, and write them to a new data
file.

.. code-block:: python

    import fiona
    from fiona import Feature, Geometry
    from shapely.geometry import mapping, shape

    # Open a file for reading. We'll call this the source.
    with fiona.open("tests/data/coutwildrnp.shp") as src:

        # The file we'll write to must be initialized with a coordinate
        # system, a format driver name, and a record schema. We can get
        # initial values from the open source's profile property and then
        # modify them as we need.
        profile = src.profile
        profile["schema"]["geometry"] = "Point"
        profile["driver"] = "GPKG"

        # Open an output file, using the same format driver and coordinate
        # reference system as the source. The profile mapping fills in the
        # keyword parameters of fiona.open.
        with fiona.open("/tmp/example.gpkg", "w", **profile) as dst:

            # Process only the records intersecting a box.
            for f in src.filter(bbox=(-107.0, 37.0, -105.0, 39.0)):

                # Get the feature's centroid.
                centroid_shp = shape(f.geometry).centroid
                new_geom = Geometry.from_dict(centroid_shp)

                # Write the feature out.
                dst.write(
                    Feature(geometry=new_geom, properties=f.properties)
                )

        # The destination's contents are flushed to disk and the file is
        # closed when its with block ends. This effectively
        # executes ``dst.flush(); dst.close()``.

CLI Usage
=========

Fiona's command line interface, named "fio", is documented at `docs/cli.rst
<https://github.com/Toblerity/Fiona/blob/master/docs/cli.rst>`__. The CLI has a
number of different commands. Its ``fio cat`` command streams GeoJSON features
from any dataset.

.. code-block:: console

    $ fio cat --compact tests/data/coutwildrnp.shp | jq -c '.'
    {"geometry":{"coordinates":[[[-111.73527526855469,41.995094299316406],...]]}}
    ...

Documentation
=============

For more details about this project, please see:

* Fiona `home page <https://github.com/Toblerity/Fiona>`__
* `Docs and manual <https://fiona.readthedocs.io/>`__
* `Examples <https://github.com/Toblerity/Fiona/tree/master/examples>`__
* Main `user discussion group <https://fiona.groups.io/g/main>`__
* `Developers discussion group <https://fiona.groups.io/g/dev>`__
