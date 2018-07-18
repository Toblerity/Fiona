Command Line Interface
======================

Fiona's new command line interface is a program named "fio".

.. code-block:: console

    Usage: fio [OPTIONS] COMMAND [ARGS]...

      Fiona command line interface.

    Options:
      -v, --verbose     Increase verbosity.
      -q, --quiet       Decrease verbosity.
      --version         Show the version and exit.
      --gdal-version    Show the version and exit.
      --python-version  Show the version and exit.
      --help            Show this message and exit.

    Commands:
      bounds   Print the extent of GeoJSON objects
      calc     Calculate GeoJSON property by Python expression
      cat      Concatenate and print the features of datasets
      collect  Collect a sequence of features.
      distrib  Distribute features from a collection.
      dump     Dump a dataset to GeoJSON.
      env      Print information about the fio environment.
      filter   Filter GeoJSON features by python expression.
      info     Print information about a dataset.
      insp     Open a dataset and start an interpreter.
      load     Load GeoJSON to a dataset in another format.
      ls       List layers in a datasource.
      rm       Remove a datasource or an individual layer.

It is developed using the ``click`` package and is new in 1.1.6.

bounds
------

New in 1.4.5.

Fio-bounds reads LF or RS-delimited GeoJSON texts, either features or
collections, from stdin and prints their bounds with or without other data to
stdout.

With no options, it works like this:

.. code-block:: console

    $ fio cat docs/data/test_uk.shp | head -n 1 \
    > | fio bounds
    [0.735, 51.357216, 0.947778, 51.444717]

Using ``--with-id`` gives you

.. code-block:: console

    $ fio cat docs/data/test_uk.shp | head -n 1 \
    > | fio bounds --with-id
    {"id": "0", "bbox": [0.735, 51.357216, 0.947778, 51.444717]}

calc
----

New in 1.7b1

The calc command creates a new property on GeoJSON features using the
specified expression.

The expression is evaluated in a restricted namespace containing 4 functions
(`sum`, `pow`, `min`, `max`), the `math` module, the shapely `shape` function,
type conversions (`bool`, `int`, `str`, `len`, `float`), and an object `f`
representing the feature to be evaluated. This `f` object allows access in
javascript-style dot notation for convenience.

The expression will be evaluated for each feature and its return value will be
added to the properties as the specified property_name. Existing properties
will not be overwritten by default (an `Exception` is raised).

.. code-block:: console

    $ fio cat data.shp | fio calc sumAB  "f.properties.A + f.properties.B"

cat
---

The cat command concatenates the features of one or more datasets and prints
them as a `JSON text sequence
<http://tools.ietf.org/html/draft-ietf-json-text-sequence-07>`__ of features.
In other words: GeoJSON feature objects, possibly pretty printed, optionally
separated by ASCII RS (\x1e) chars using `--rs`.

The output of ``fio cat`` can be piped to ``fio load`` to create new
concatenated datasets.

.. code-block:: console

    $ fio cat docs/data/test_uk.shp docs/data/test_uk.shp \
    > | fio load /tmp/double.shp --driver Shapefile
    $ fio info /tmp/double.shp --count
    96
    $ fio info docs/data/test_uk.shp --count
    48

New in 1.4.0.

collect
-------

The collect command takes a JSON text sequence of GeoJSON feature objects, such
as the output of ``fio cat`` and writes a GeoJSON feature collection.

.. code-block:: console

    $ fio cat docs/data/test_uk.shp docs/data/test_uk.shp \
    > | fio collect > /tmp/collected.json
    $ fio info /tmp/collected.json --count
    96

New in 1.4.0.

distrib
-------

The inverse of fio-collect, fio-distrib takes a GeoJSON feature collection
and writes a JSON text sequence of GeoJSON feature objects.

.. code-block:: console

    $ fio info --count tests/data/coutwildrnp.shp
    67
    $ fio cat tests/data/coutwildrnp.shp | fio collect | fio distrib | wc -l
    67

New in 1.4.0.

dump
----

The dump command reads a vector dataset and writes a GeoJSON feature collection
to stdout. Its output can be piped to ``fio load`` (see below).

.. code-block:: console

    $ fio dump docs/data/test_uk.shp --indent 2 --precision 2 | head
    {
      "features": [
        {
          "geometry": {
            "coordinates": [
              [
                [
                  0.9,
                  51.36
                ],

You can optionally dump out JSON text sequences using ``--x-json-seq``. Since
version 1.4.0, ``fio cat`` is the better tool for generating sequences.

.. code-block:: console

    $ fio dump docs/data/test_uk.shp --precision 2 --x-json-seq | head -n 2
    {"geometry": {"coordinates": [[[0.9, 51.36], [0.89, 51.36], [0.79, 51.37], [0.78, 51.37], [0.77, 51.38], [0.76, 51.38], [0.75, 51.39], [0.74, 51.4], [0.73, 51.41], [0.74, 51.43], [0.75, 51.44], [0.76, 51.44], [0.79, 51.44], [0.89, 51.42], [0.9, 51.42], [0.91, 51.42], [0.93, 51.4], [0.94, 51.39], [0.94, 51.38], [0.95, 51.38], [0.95, 51.37], [0.95, 51.37], [0.94, 51.37], [0.9, 51.36], [0.9, 51.36]]], "type": "Polygon"}, "id": "0", "properties": {"AREA": 244820.0, "CAT": 232.0, "CNTRY_NAME": "United Kingdom", "FIPS_CNTRY": "UK", "POP_CNTRY": 60270708.0}, "type": "Feature"}
    {"geometry": {"coordinates": [[[-4.66, 51.16], [-4.67, 51.16], [-4.67, 51.16], [-4.67, 51.17], [-4.67, 51.19], [-4.67, 51.19], [-4.67, 51.2], [-4.66, 51.2], [-4.66, 51.19], [-4.65, 51.16], [-4.65, 51.16], [-4.65, 51.16], [-4.66, 51.16]]], "type": "Polygon"}, "id": "1", "properties": {"AREA": 244820.0, "CAT": 232.0, "CNTRY_NAME": "United Kingdom", "FIPS_CNTRY": "UK", "POP_CNTRY": 60270708.0}, "type": "Feature"}


info
----

The info command prints information about a dataset as a JSON object.

.. code-block:: console

    $ fio info docs/data/test_uk.shp --indent 2
    {
      "count": 48,
      "crs": "+datum=WGS84 +no_defs +proj=longlat",
      "driver": "ESRI Shapefile",
      "bounds": [
        -8.621389,
        49.911659,
        1.749444,
        60.844444
      ],
      "schema": {
        "geometry": "Polygon",
        "properties": {
          "CAT": "float:16",
          "FIPS_CNTRY": "str:80",
          "CNTRY_NAME": "str:80",
          "AREA": "float:15.2",
          "POP_CNTRY": "float:15.2"
        }
      }
    }

You can process this JSON using, e.g., 
`underscore-cli <https://github.com/ddopson/underscore-cli>`__.

.. code-block:: console

    $ fio info docs/data/test_uk.shp | underscore extract count
    48

You can also optionally get single info items as plain text (not JSON) 
strings

.. code-block:: console

    $ fio info docs/data/test_uk.shp --count
    48
    $ fio info docs/data/test_uk.shp --bounds
    -8.621389 49.911659 1.749444 60.844444

load
----

The load command reads GeoJSON features from stdin and writes them to a vector
dataset using another format.

.. code-block:: console

    $ fio dump docs/data/test_uk.shp \
    > | fio load /tmp/test.shp --driver Shapefile

This command also supports GeoJSON text sequences. RS-separated sequences will
be detected. If you want to load LF-separated sequences, you must specfiy
``--x-json-seq``.

.. code-block:: console

    $ fio cat docs/data/test_uk.shp | fio load /tmp/foo.shp --driver Shapefile
    $ fio info /tmp/foo.shp --indent 2
    {
      "count": 48,
      "crs": "+datum=WGS84 +no_defs +proj=longlat",
      "driver": "ESRI Shapefile",
      "bounds": [
        -8.621389,
        49.911659,
        1.749444,
        60.844444
      ],
      "schema": {
        "geometry": "Polygon",
        "properties": {
          "AREA": "float:24.15",
          "CNTRY_NAME": "str:80",
          "POP_CNTRY": "float:24.15",
          "FIPS_CNTRY": "str:80",
          "CAT": "float:24.15"
        }
      }
    }

The underscore-cli process command is another way of turning a GeoJSON feature
collection into a feature sequence.

.. code-block:: console

    $ fio dump docs/data/test_uk.shp \
    > | underscore process \
    > 'each(data.features,function(o){console.log(JSON.stringify(o))})' \
    > | fio load /tmp/test-seq.shp --x-json-seq --driver Shapefile


filter
------
The filter command reads GeoJSON features from stdin and writes the feature to 
stdout *if* the provided expression evalutates to `True` for that feature. 

The python expression is evaluated in a restricted namespace containing 3 functions 
(`sum`, `min`, `max`), the `math` module, the shapely `shape` function, 
and an object `f` representing the feature to be evaluated. This `f` object allows
access in javascript-style dot notation for convenience. 

If the expression evaluates to a "truthy" value, the feature is printed verbatim.
Otherwise, the feature is excluded from the output.

.. code-block:: console

    $ fio cat data.shp \
    > | fio filter "f.properties.area > 1000.0" \
    > | fio collect > large_polygons.geojson

Would create a geojson file with only those features from `data.shp` where the
area was over a given threshold.

rm
--
The ``fio rm`` command deletes an entire datasource or a single layer in a
multi-layer datasource. If the datasource is composed of multiple files
(e.g. an ESRI Shapefile) all of the files will be removed.

.. code-block:: console

    $ fio rm countries.shp
    $ fio rm --layer forests land_cover.gpkg

New in 1.8.0.

Coordinate Reference System Transformations
-------------------------------------------

The ``fio cat`` command can optionally transform feature geometries to a new
coordinate reference system specified with ``--dst_crs``. The ``fio collect``
command can optionally transform from a coordinate reference system specified
with ``--src_crs`` to the default WGS84 GeoJSON CRS. Like collect, ``fio load``
can accept non-WGS84 features, but as it can write files in formats other than
GeoJSON, you can optionally specify a ``--dst_crs``. For example, the WGS84
features read from docs/data/test_uk.shp,

.. code-block:: console

     $ fio cat docs/data/test_uk.shp --dst_crs EPSG:3857 \
     > | fio collect --src_crs EPSG:3857 > /tmp/foo.json

make a detour through EPSG:3857 (Web Mercator) and are transformed back to WGS84
by fio cat. The following,

.. code-block:: console

    $ fio cat docs/data/test_uk.shp --dst_crs EPSG:3857 \
    > | fio load --src_crs EPSG:3857 --dst_crs EPSG:4326 --driver Shapefile \
    > /tmp/foo.shp

does the same thing, but for ESRI Shapefile output.

New in 1.4.2.
