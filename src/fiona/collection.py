# Collections provide file-like access to feature data

import os

from fiona.ogrext import Iterator, Session, WritingSession


class Collection(object):

    """A file-like interface to features in the form of GeoJSON-like
    mappings."""

    def __init__(
            self, path, mode='r', 
            driver=None, schema=None, crs=None, workspace=None):
        
        """The required ``path`` is the absolute or relative path to
        a file, such as '/data/test_uk.shp'. In ``mode`` 'r', data can
        be read only. In ``mode`` 'a', data can be appended to a file.
        In ``mode`` 'w', data overwrites the existing contents of
        a file.
        
        In ``mode`` 'w', an OGR ``driver`` name and a ``schema`` are
        required. A Proj4 ``crs`` string is recommended.
        """

        self.session = None
        self.iterator = None
        self._buffer = []
        self._len = 0
        self._bounds = None
        self._driver = None
        self._schema = None
        self._crs = None
        self.path = path
        self.name = os.path.basename(os.path.splitext(path)[0])
        self.mode = mode
        if driver:
            self._driver = driver
        if schema:
            self._schema = schema
        if crs:
            self._crs = crs
        self.workspace = workspace
        if self.mode == "r":
            self.session = Session()
            self.session.start(self)
        elif self.mode in ("a", "w"):
            self.session = WritingSession()
            self.session.start(self)

    @property 
    def driver(self):
        """Returns the name of the proper OGR driver."""
        if not self._driver and self.mode in ("a", "r"):
            self._driver = self.session.get_driver()
        return self._driver

    @property 
    def schema(self):
        """Returns a mapping describing the data schema."""
        if not self._schema and self.mode in ("a", "r"):
            self._schema = self.session.get_schema()
        return self._schema

    @property
    def crs(self):
        """Returns a Proj4 string."""
        if self._crs is None and self.mode in ("a", "r"):
            self._crs = self.session.get_crs()
        return self._crs

    def filter(self, bbox=None):
        """Returns an iterator over records, but filtered by a test for
        spatial intersection with the provided ``bbox``, a (minx, miny,
        maxx, maxy) tuple."""
        if self.closed:
            raise ValueError("Collection is not open for reading")
        elif self.mode != 'r':
            raise IOError("Collection is not open for reading")
        if self.iterator is None:
            self.iterator = Iterator(self, bbox)
        return self.iterator

    def __iter__(self):
        """Returns an iterator over records."""
        return self.filter()

    def next(self):
        """Returns next record from iterator."""
        return iter(self).next()

    def writerecords(self, records):
        """Stages multiple records for writing to disk."""
        if self.mode not in ('a', 'w'):
            raise IOError("Collection is not open for reading")
        self._buffer.extend(list(records))

    def write(self, record):
        """Stages a record for writing to disk."""
        self.writerecords([record])

    def _flushbuffer(self):
        if self.session is not None and len(self._buffer) > 0:
            self.session.writerecs(self._buffer, self)
            self.session.sync()
            new_len = self.session.get_length()
            self._len = new_len > self._len \
                and new_len or self._len + len(self._buffer)
            self._buffer = []
            self._bounds = self.session.get_extent()

    def __len__(self):
        if self._len <= 0 and self.session is not None:
            self._len = self.session.get_length()
        self._flushbuffer()
        return self._len

    @property
    def bounds(self):
        """Returns (minx, miny, maxx, maxy)."""
        if self._bounds is None and self.session is not None:
            self._bounds = self.session.get_extent()
        self._flushbuffer()
        return self._bounds

    def flush(self):
        """Flush the buffer."""
        self._flushbuffer()

    def close(self):
        """In append or write mode, flushes data to disk, then ends
        access."""
        if self.session is not None: 
            if self.mode in ('a', 'w'):
                self._flushbuffer()
            self.session.stop()
            self.session = None
            self.iterator = None

    @property
    def closed(self):
        """``False`` if data can be accessed, otherwise ``True``."""
        return self.session is None

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()
        self.workspace = None

    def __del__(self):
        # Note: you can't count on this being called. Call close() explicitly
        # or use the context manager protocol ("with").
        self.__exit__(None, None, None)

