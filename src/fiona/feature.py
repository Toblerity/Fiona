# Copyright (c) 2007, Sean C. Gillies
# All rights reserved.
# See ../LICENSE.txt

class Feature(object):

    id = None
    properties = None
    geometry = None

    def __init__(self, id, properties, geometry):
        self.id = id
        if properties:
            self.properties = properties.copy()
        self.geometry = geometry


def feature(id, properties, wkb):
    return Feature(id, properties, wkb)

