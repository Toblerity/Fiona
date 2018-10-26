"""Do not delete!  At least one of the ``unittest.TestCase()`` based tests do
a relative import inside the ``tests`` directory to use another test as a
base class.  This file can probably be deleted if that condition is removed.

For example:

    $ git grep 'from \.' | grep test
    tests/test_layer.py:from .test_collection import TestReading
    tests/test_vfs.py:from .test_collection import TestReading
"""
