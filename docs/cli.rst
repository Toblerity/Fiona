Command Line Interface
======================

Fiona's new command line interface is a program named "fio".

.. code-block:: console

    $ fio
    Usage: fio [OPTIONS] COMMAND [ARGS]...

      Fiona command line interface.

    Options:
      -v, --verbose  Increase verbosity.
      -q, --quiet    Decrease verbosity.
      --help         Show this message and exit.

    Commands:
      info       Print information about a data file.
      insp       Open a data file and start an interpreter.
      translate  Translate GeoJSON to another vector format.

It is developed using the ``click`` package and is new in 1.1.6.

info
----

The info command prints information about a data file as a JSON object.

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
[underscore-cli](https://github.com/ddopson/underscore-cli).

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

dump
----

The dump command reads a vector dataset and writes its features to stdout
using GeoJSON.

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

load
----

The load command reads GeoJSON features from stdin and writes them to a
vector dataset using another format.

.. code-block:: console

    $ fio dump docs/data/test_uk.shp \
    > | fio -qq load /tmp/test.shp --driver "ESRI Shapefile"
    $ ls -l /tmp/test.*
    -rw-r--r--  1 sean  wheel     10 Sep  6 23:27 /tmp/test.cpg
    -rw-r--r--  1 sean  wheel  11377 Sep  6 23:27 /tmp/test.dbf
    -rw-r--r--  1 sean  wheel    143 Sep  6 23:27 /tmp/test.prj
    -rw-r--r--  1 sean  wheel  65156 Sep  6 23:27 /tmp/test.shp
    -rw-r--r--  1 sean  wheel    484 Sep  6 23:27 /tmp/test.shx

This command supports `JSON text sequences <http://tools.ietf.org/html/draft-ietf-json-text-sequence-04>`__ as an experimental feature. The underscore-cli
process command is one way of turning a GeoJSON file into a text sequence.

.. code-block:: console

    $ fio dump docs/data/test_uk.shp \
    > | underscore process \
    > 'each(data.features,function(o){console.log(JSON.stringify(o))})' \
    > | fio load /tmp/test-seq.shp --x-json-seq --driver "ESRI Shapefile"
    $ ls -l /tmp/test-seq.*
    -rw-r--r--  1 sean  wheel     10 Sep  6 23:31 /tmp/test-seq.cpg
    -rw-r--r--  1 sean  wheel   9361 Sep  6 23:31 /tmp/test-seq.dbf
    -rw-r--r--  1 sean  wheel    143 Sep  6 23:31 /tmp/test-seq.prj
    -rw-r--r--  1 sean  wheel  65156 Sep  6 23:31 /tmp/test-seq.shp
    -rw-r--r--  1 sean  wheel    484 Sep  6 23:31 /tmp/test-seq.shx
