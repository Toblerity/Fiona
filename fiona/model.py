"""Fiona data model"""

from collections.abc import MutableMapping
from warnings import warn

from fiona.errors import FionaDeprecationWarning


class Object(MutableMapping):
    """Base class for CRS, geometry, and feature objects

    In Fiona 2.0, the implementation of those objects will change.  They
    will no longer be dicts or derive from dict, and will lose some
    features like mutability and default JSON serialization.

    Object will be used for these objects in Fiona 1.9. This class warns
    about future deprecation of features.
    """

    def __init__(self, **data):
        self._data = {}
        self._data.update(data)

    def __getitem__(self, item):
        return self._data[item]

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __setitem__(self, key, value):
        warn(
            "instances of this class -- CRS, geometry, and feature objects -- will become immutable in fiona version 2.0",
            FionaDeprecationWarning,
            stacklevel=2,
        )
        self._data[key] = value

    def __delitem__(self, key):
        warn(
            "instances of this class -- CRS, geometry, and feature objects -- will become immutable in fiona version 2.0",
            FionaDeprecationWarning,
            stacklevel=2,
        )
        del self._data[key]


class Geometry(Object):
    """A GeoJSON-like geometry
    """

    @property
    def coordinates(self):
        """The geometry's coordinates

        Returns
        -------
        Sequence

        """
        return self._data.get("coordinates", None)

    @property
    def type(self):
        """The geometry's type

        Returns
        -------
        str

        """
        return self._data.get("type", None)


class Feature(Object):
    """A GeoJSON-like feature
    """

    @property
    def geometry(self):
        """The feature's geometry object

        Returns
        -------
        Geometry

        """
        return Geometry(**self._data.get("geometry", {}))

    @property
    def id(self):
        """The feature's id

        Returns
        ------
        obejct

        """
        return self._data.get("id", None)

    @property
    def properties(self):
        """The feature's properties

        Returns
        -------
        Object

        """
        return Object(**self._data.get("properties", {}))

    @property
    def type(self):
        """The Feature's type

        Returns
        -------
        str

        """
        return self._data.get("type", None)
