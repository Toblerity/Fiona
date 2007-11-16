WorldMill
=========

Access and transform geospatial feature data.

See docs/reading-data.txt for examples.


Building
--------

From the distribution root::

  $ ./cypsrc
  $ python setup.py build_ext --inplace
  $ PYTHONPATH=src python tests.py

Benchmarks
----------

If you have ogr.py installed, you can compare to WorldMill::

  $ PYTHONPATH=src python benchmark.py


