
import fiona

# This module contains examples of opening files to get feature collections in
# different ways.
#
# It is meant to be run from the distribution root, the directory containing
# setup.py.
#
# A ``path`` is always the ``open()`` function's first argument. It can be
# absolute or relative to the working directory. It is the only positional
# argument, though it is conventional to use the mode as a 2nd positional
# argument.

# 1. Opening a file with a single data layer (shapefiles, etc).
#
# args: path, mode
# kwds: none
#
# The relative path to a file on the filesystem is given and its single layer
# is selected implicitly (a shapefile has a single layer). The file is opened
# for reading (mode 'r'), but since this is the default, we'll omit it in
# following examples.

with fiona.open('docs/data/test_uk.shp', 'r') as c:
    assert len(c) == 48

# 2. Opening a file with explicit layer selection (FileGDB, etc).
#
# args: path
# kwds: layer
#
# Same as above but layer specified explicitly by name..

with fiona.open('docs/data/test_uk.shp', layer='test_uk') as c:
    assert len(c) == 48

# 3. Opening a directory for access to a single file.
#
# args: path
# kwds: layer
#
# Same as above but using the path to the directory containing the shapefile,
# specified explicitly by name.

with fiona.open('docs/data', layer='test_uk') as c:
    assert len(c) == 48

# 4. Opening a single file within a zip archive.
#
# args: path
# kwds: vfs
#
# Open a file given its absolute path within a virtual filesystem. The VFS
# is given an Apache Commons VFS identifier. It may contain either an absolute
# path or a path relative to the working directory.
#
# Example archive:
#
# $ unzip -l docs/data/test_uk.zip
# Archive:  docs/data/test_uk.zip
#   Length     Date   Time    Name
#  --------    ----   ----    ----
#     10129  04-08-13 20:49   test_uk.dbf
#       143  04-08-13 20:49   test_uk.prj
#     65156  04-08-13 20:49   test_uk.shp
#       484  04-08-13 20:49   test_uk.shx
#  --------                   -------
#     75912                   4 files

with fiona.open('/test_uk.shp', vfs='zip://docs/data/test_uk.zip') as c:
    assert len(c) == 48

# 5. Opening a directory within a zip archive to select a layer.
#
# args: path
# kwds: layer, vfs
#
# The most complicated case. As above, but specifying the root directory within
# the virtual filesystem as the path and the layer by name (combination of
# 4 and 3). It ought to be possible to open a file geodatabase within a zip
# file like this.

with fiona.open('/', layer='test_uk', vfs='zip://docs/data/test_uk.zip') as c:
    assert len(c) == 48

