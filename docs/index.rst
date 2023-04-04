===============================================
Fiona: access to simple geospatial feature data
===============================================

Fiona streams simple feature data to and from GIS formats like GeoPackage and
Shapefile. Simple features are record, or row-like, and have a single geometry
attribute. Fiona can read and write real-world simple feature data using
multi-layered GIS formats, zipped and in-memory virtual file systems, from
files on your hard drive or in cloud storage. This project includes Python
modules and a command line interface (CLI).

Here's an example of streaming and filtering features from a zipped dataset on
the web and saving them to a new layer in a new Geopackage file.

.. code-block:: python

    import fiona

    with fiona.open(
        "zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip"
    ) as src:
        profile = src.profile
        profile["driver"] = "GPKG"

        with fiona.open("example.gpkg", "w", layer="selection", **profile) as dst:
            dst.writerecords(feat in src.filter(bbox=(-107.0, 37.0, -105.0, 39.0)))

The same result can be achieved on the command line using a combination of
fio-cat and fio-load.

.. code-block:: console

    fio cat zip+https://github.com/Toblerity/Fiona/files/11151652/coutwildrnp.zip --bbox "-107.0,37.0,-105.0,39.0" \
    | fio load -f GPKG --layer selection example.gpkg

.. toctree::
   :maxdepth: 2

   Project Information <README>
   Installation <install>
   User Manual <manual>
   API Documentation <modules>
   CLI Documentation <cli>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

