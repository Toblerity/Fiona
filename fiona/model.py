"""Fiona data model"""

from collections.abc import MutableMapping
from collections import OrderedDict
import itertools
from json import JSONEncoder
from warnings import warn

from fiona.errors import FionaDeprecationWarning
from fiona.compat import MutableMapping


# Mapping of OGR integer geometry types to GeoJSON type names.
GEOMETRY_TYPES = {
    0: "Unknown",
    1: "Point",
    2: "LineString",
    3: "Polygon",
    4: "MultiPoint",
    5: "MultiLineString",
    6: "MultiPolygon",
    7: "GeometryCollection",
    # Unsupported types.
    # 8: 'CircularString',
    # 9: 'CompoundCurve',
    # 10: 'CurvePolygon',
    # 11: 'MultiCurve',
    # 12: 'MultiSurface',
    # 13: 'Curve',
    # 14: 'Surface',
    # 15: 'PolyhedralSurface',
    # 16: 'TIN',
    # 17: 'Triangle',
    100: "None",
    101: "LinearRing",
    0x80000001: "3D Point",
    0x80000002: "3D LineString",
    0x80000003: "3D Polygon",
    0x80000004: "3D MultiPoint",
    0x80000005: "3D MultiLineString",
    0x80000006: "3D MultiPolygon",
    0x80000007: "3D GeometryCollection",
}


# Mapping of OGR integer geometry types to GeoJSON type names.
GEOMETRY_TYPES = {
    0: "Unknown",
    1: "Point",
    2: "LineString",
    3: "Polygon",
    4: "MultiPoint",
    5: "MultiLineString",
    6: "MultiPolygon",
    7: "GeometryCollection",
    # Unsupported types.
    # 8: 'CircularString',
    # 9: 'CompoundCurve',
    # 10: 'CurvePolygon',
    # 11: 'MultiCurve',
    # 12: 'MultiSurface',
    # 13: 'Curve',
    # 14: 'Surface',
    # 15: 'PolyhedralSurface',
    # 16: 'TIN',
    # 17: 'Triangle',
    100: "None",
    101: "LinearRing",
    0x80000001: "3D Point",
    0x80000002: "3D LineString",
    0x80000003: "3D Polygon",
    0x80000004: "3D MultiPoint",
    0x80000005: "3D MultiLineString",
    0x80000006: "3D MultiPolygon",
    0x80000007: "3D GeometryCollection",
}


class Object(MutableMapping):
    """Base class for CRS, geometry, and feature objects

    In Fiona 2.0, the implementation of those objects will change.  They
    will no longer be dicts or derive from dict, and will lose some
    features like mutability and default JSON serialization.

    Object will be used for these objects in Fiona 1.9. This class warns
    about future deprecation of features.
    """

    _delegated_properties = []

    def __init__(self, **kwds):
        self._data = OrderedDict(**kwds)

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

    @classmethod
    def from_dict(cls, mapping=None, **kwargs):
        data = dict(mapping or {}, **kwargs)
        return Geometry(
            coordinates=data.pop("coordinates", None),
            type=data.pop("type", None),
            **data
        )

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
    def from_dict(cls, mapping=None, **kwargs):
        data = dict(mapping or {}, **kwargs)
        geom_data = data.pop("geometry", None)

        if isinstance(geom_data, Geometry):
            geom = geom_data
        else:
            geom = (
                Geometry(
                    coordinates=geom_data.pop("coordinates", None),
                    type=geom_data.pop("type", None),
                    **geom_data
                )
                if geom_data is not None
                else None
            )

        props_data = data.pop("properties", None)

        if isinstance(props_data, Properties):
            props = props_data
        else:
            props = Properties(**props_data) if props_data is not None else None

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


class Properties(Object):
    """A GeoJSON-like feature's properties

    """

    def __init__(self, **kwds):
        super(Properties, self).__init__(**kwds)

    @classmethod
    def from_dict(cls, mapping=None, **kwargs):
        data = dict(mapping or {}, **kwargs)
        return Properties(**data)


class ObjectEncoder(JSONEncoder):
    """Encodes Geometry and Feature"""

    def default(self, o):
        if isinstance(o, (Geometry, Properties)):
            return dict(**o)
        elif isinstance(o, Feature):
            o_dict = dict(**o)
            o_dict["type"] = "Feature"
            if o.geometry is not None:
                o_dict["geometry"] = ObjectEncoder().default(o.geometry)
            if o.properties is not None:
                o_dict["properties"] = ObjectEncoder().default(o.properties)
            return o_dict
        else:
            return JSONEncoder().default(o)


def decode_object(o):
    """A json.loads object_hook

    Parameters
    ----------
    o : dict
        A decoded dict.

    Returns
    -------
    Feature, Geometry, or dict

    """
    if "type" in o:
        if o["type"] == "Feature":
            val = Feature.from_dict(**o)
        elif o["type"] in list(GEOMETRY_TYPES.values())[:8]:
            val = Geometry.from_dict(**o)
        else:
            val = o
    else:
        val = o

    return val


def to_dict(val):
    """Converts an object to a dict"""
    try:
        o = ObjectEncoder().default(val)
    except TypeError:
        pass
    else:
        return o

    return val
