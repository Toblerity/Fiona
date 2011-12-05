# Copyright (c) 2007, Sean C. Gillies
# All rights reserved.
# See ../LICENSE.txt

#from fiona.wkb import loads
from cPickle import loads

class Feature(object):

    id = None
    properties = None
    geometry = None

    def __init__(self, id, properties, geometry):
        self.id = id
        if properties:
            self.properties = properties.copy()
        self.geometry = geometry

    @property
    def __geo_interface__(self):
        return {
            'type': "Feature", 
            'id': self.id,
            'properties': self.properties,
            'geometry': self.geometry.__geo_interface__}


class Geometry(object):
    # One or more coordinate array parts and a geometry type to distinguish
    # between line strings and multipoints
    def __init__(self, type, parts=None):
        self.type = type
        self.parts = parts or []

    @property
    def coordinates(self):
        if len(parts) == 0:
            return None
        elif len(parts) == 1:
            part = parts[0]
            if len(part.xs) == len(part.ys) == 1 and self.type == 'Point':
                return (part.xs[0], part.ys[0])
            else:
                return zip(part.xs, part.ys)
        else:
            value = []
            for part in parts:
                value.append(zip(part.xs, part.ys))
            return value
        
    @property
    def __geo_interface__(self):
        return {'type': self.type, 'coordinates': self.coordinates}


class Part(object):
    # Just a pair of coordinate arrays
    def __init__(self, coordinates=None):
        self.xs = None
        self.ys = None
        if coordinates:
            xs, ys = zip(*coordinates)
            self.xs = array('d', xs)
            self.ys = array('d', ys)


def feature(id, properties, wkb):
    return Feature(id, properties, loads(wkb))

