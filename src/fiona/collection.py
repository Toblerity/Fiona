# Collections provide file-like access to feature data

import os

from fiona.ogrext import Iterator, Session, WritingSession


class Collection(object):

    """A file-like interface to features in the form of GeoJSON-like mappings."""

    def __init__(self, path, mode='r', driver=None, schema=None, workspace=None):
        """The required ``path`` is the absolute or relative path to a file, such
        as '/data/test_uk.shp'. In ``mode`` 'r', data can be read only. In ``mode``
        'a', data can be appended to a file. In ``mode`` 'w', data overwrites the
        existing contents of a file."""
        self.session = None
        self._len = -1
        self._schema = None
        self.path = path
        self.name = os.path.basename(os.path.splitext(path)[0])
        self.mode = mode
        self.driver = driver
        if schema:
            self._schema = schema
        self.workspace = workspace

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if self.session:
            self.close()
        self.workspace = None

    def __len__(self):
        if self._len < 0:
            self._len = self.session.get_length()
        return self._len

    def open(self):
        """Begins access to data."""
        if self.session is not None:
            raise IOError("Collection is already open")
        if self.mode == "r":
            self.session = Session()
            self.session.start(self)
        elif self.mode in ("a", "w"):
            self.session = WritingSession()
            self.session.start(self)

    def close(self):
        """In append or write mode, flushes data to disk, then ends access."""
        if self.session is None:
            raise IOError("Collection is not open")
        self.session.stop()
        self.session = None

    @property
    def opened(self):
        """``True`` if data can be accessed, otherwise ``False``."""
        return self.session is not None

    @property 
    def schema(self):
        """Returns a mapping describing the data schema"""
        if not self._schema:
            self._schema = self.session.get_schema()
        return self._schema

    def __iter__(self):
        """Returns an iterator over GeoJSON-like mappings of features"""
        if self.mode != 'r':
            raise IOError("Collection is not open for reading")
        return Iterator(self)

    def filter(self, bbox=None):
        """Returns an iterator over GeoJSON-like mappings of features, but 
        filtered by a test for spatial intersection with the provided ``bbox``,
        a (minx, miny, maxx, maxy) tuple."""
        if self.mode != 'r':
            raise IOError("Collection is not open for reading")
        return Iterator(self, bbox)

    def write(self, feature):
        """Stages a GeoJSON-like feature mapping for writing to disk."""
        if self.mode not in ('a', 'w'):
            raise IOError("Collection is not open for reading")
        self.session.write(feature, self)

