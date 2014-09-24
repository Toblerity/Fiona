Command Line Interface
======================

Fiona's new command line interface is a program named "fio".

.. code-block:: console

    Usage: fio [OPTIONS] COMMAND [ARGS]...

      Fiona command line interface.

    Options:
      -v, --verbose  Increase verbosity.
      -q, --quiet    Decrease verbosity.
      --help         Show this message and exit.

    Commands:
      cat      Concatenate and print the features of datasets
      collect  Collect a sequence of features.
      dump     Dump a dataset to GeoJSON.
      info     Print information about a dataset.
      insp     Open a dataset and start an interpreter.
      load     Load GeoJSON to a dataset in another format.

It is developed using the ``click`` package and is new in 1.1.6.

cat
---

The cat command concatenates the features of one or more datasets and prints
them as a `JSON text sequence
<http://tools.ietf.org/html/draft-ietf-json-text-sequence-07>`__ of features.
In other words: GeoJSON feature objects, possibly pretty printed, separated by
ASCII RS (\x1e) chars. LF-separated sequences with no pretty printing are
optionally available using ``--x-json-seq-no-rs``.

The output of ``fio cat`` can be piped to ``fio load`` to create new
concatenated datasets.

.. code-block:: console

    $ fio cat docs/data/test_uk.shp docs/data/test_uk.shp \
    > | fio load /tmp/double.shp --driver "ESRI Shapefile"
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

dump
----

The dump command reads a vector dataset and writes a GeoJSON feature collection
to stdout. Its output can be piped to ``rio load`` (see below).

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
    > | fio load /tmp/test.shp --driver "ESRI Shapefile"

This command also supports GeoJSON text sequences. RS-separated sequences will
be detected. If you want to load LF-separated sequences, you must specfiy
``--x-json-seq``.

.. code-block:: console

    $ fio cat docs/data/test_uk.shp | fio load /tmp/foo.shp --driver "ESRI Shapefile"
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
    > | fio load /tmp/test-seq.shp --x-json-seq --driver "ESRI Shapefile"
