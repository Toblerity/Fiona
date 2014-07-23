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
      translate  Translate GeoJSON to another vector format.

It is developed using the ``click`` package and is new in 1.1.6.

translate
---------

The translate command read GeoJSON input and writes a vector dataset using
another format.

.. code-block:: console

    $ cat docs/data/test_uk.json | fio translate - /tmp/test.shp --driver "ESRI Shapefile"
    $ ls -l /tmp/test.*
    -rw-r--r--  1 sean  wheel     10 Jul 23 15:09 /tmp/test.cpg
    -rw-r--r--  1 sean  wheel  11377 Jul 23 15:09 /tmp/test.dbf
    -rw-r--r--  1 sean  wheel    143 Jul 23 15:09 /tmp/test.prj
    -rw-r--r--  1 sean  wheel  65156 Jul 23 15:09 /tmp/test.shp
    -rw-r--r--  1 sean  wheel    484 Jul 23 15:09 /tmp/test.shx

This command supports `JSON text sequences <http://tools.ietf.org/html/draft-ietf-json-text-sequence-04>`__ as an experimental feature. Underscore-cli's
process command is one way of turning a GeoJSON file into a text sequence.

.. code-block:: console

    $ underscore -i docs/data/test_uk.json process 'each(data.features,function(o){console.log(JSON.stringify(o))})' | fio translate - /tmp/test2.json --driver "ESRI Shapefile" --x-json-seq
    $ ls -l /tmp/test2.*
    -rw-r--r--  1 sean  wheel     10 Jul 23 15:50 test2.cpg
    -rw-r--r--  1 sean  wheel   9361 Jul 23 15:50 test2.dbf
    -rw-r--r--  1 sean  wheel    143 Jul 23 15:50 test2.prj
    -rw-r--r--  1 sean  wheel  65156 Jul 23 15:50 test2.shp
    -rw-r--r--  1 sean  wheel    484 Jul 23 15:50 test2.shx

