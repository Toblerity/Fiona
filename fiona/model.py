"""Fiona data model"""

from collections.abc import MutableMapping
import itertools
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

    _delegated_properties = []

    def __init__(self, **data):
        self._data = {}
        self._data.update(**data)

    def _props(self):
        return {
            k: getattr(self._delegate, k)
            for k in self._delegated_properties
            if k is not None
        }

    def __getitem__(self, item):
        props = self._props()
        props.update(**self._data)
        return props[item]

    def __iter__(self):
        props = self._props()
        return itertools.chain(iter(props), iter(self._data))

    def __len__(self):
        props = self._props()
        return len(props) + len(self._data)

    def __setitem__(self, key, value):
        warn(
            "instances of this class -- CRS, geometry, and feature objects -- will become immutable in fiona version 2.0",
            FionaDeprecationWarning,
            stacklevel=2,
        )
        if key in self._delegated_properties:
            setattr(self._delegate, key, value)
        else:
            self._data[key] = value

    def __delitem__(self, key):
        warn(
            "instances of this class -- CRS, geometry, and feature objects -- will become immutable in fiona version 2.0",
            FionaDeprecationWarning,
            stacklevel=2,
        )
        if key in self._delegated_properties:
            setattr(self._delegate, key, None)
        else:
            del self._data[key]


class _Geometry(object):
    def __init__(self, coordinates=None, type=None):
        self.coordinates = coordinates
        self.type = type


class Geometry(Object):
    """A GeoJSON-like geometry

    Notes
    -----
    Delegates coordinates and type properties to an instance of
    _Geometry, which will become an extension class in Fiona 2.0.

    """

    _delegated_properties = ["coordinates", "type"]

    def __init__(self, coordinates=None, type=None, **data):
        self._delegate = _Geometry(coordinates=coordinates, type=type)
        super(Geometry, self).__init__(**data)

    @property
    def coordinates(self):
        """The geometry's coordinates

        Returns
        -------
        Sequence

        """
        return self._delegate.coordinates

    @property
    def type(self):
        """The geometry's type

        Returns
        -------
        str

        """
        return self._delegate.type


class _Feature(object):
    def __init__(self, geometry=None, id=None, properties=None):
        self.geometry = geometry
        self.id = id
        self.properties = properties


class Feature(Object):
    """A GeoJSON-like feature

    Notes
    -----
    Delegates geometry and properties to an instance of _Feature, which
    will become an extension class in Fiona 2.0.

    """

    _delegated_properties = ["geometry", "id", "properties"]

    def __init__(self, geometry=None, id=None, properties=None, **data):
        self._delegate = _Feature(geometry=geometry, id=id, properties=properties)
        super(Feature, self).__init__(**data)

    @classmethod
    def from_dict(cls, **data):
        data = data.copy()
        geom_data = data.pop("geometry", None)
        geom = (
            Geometry(
                coordinates=geom_data.pop("coordinates", None),
                type=geom_data.pop("type", None),
                **geom_data
            )
            if geom_data
            else None
        )
        props_data = data.pop("properties", None)
        props = Object(**props_data) if props_data else None
        fid = data.pop("id", None)
        return Feature(geometry=geom, id=fid, properties=props, **data)

    @property
    def geometry(self):
        """The feature's geometry object

        Returns
        -------
        Geometry

        """
        return self._delegate.geometry

    @property
    def id(self):
        """The feature's id

        Returns
        ------
        obejct

        """
        return self._delegate.id

    @property
    def properties(self):
        """The feature's properties

        Returns
        -------
        Object

        """
        return self._delegate.properties

    @property
    def type(self):
        """The Feature's type

        Returns
        -------
        str

        """
        return "Feature"
