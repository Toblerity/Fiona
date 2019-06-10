"""Fiona data model"""

from collections.abc import MutableMapping
from warnings import warn

from fiona.errors import FionaDeprecationWarning


class Object(MutableMapping):

    def __init__(self, **data):
        self._data = data.copy()

    def __getitem__(self, item):
        return self._data[item]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __setitem__(self, key, value):
        warn("Object will become immutable in version 2.0", FionaDeprecationWarning, stacklevel=2)
        self._data[key] = value

    def __delitem__(self, key):
        warn("Object will become immutable in version 2.0", FionaDeprecationWarning, stacklevel=2)
        del self._data[key]
