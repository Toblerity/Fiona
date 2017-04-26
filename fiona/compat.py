import collections
from six.moves import UserDict
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict


# Users can pass in objects that subclass a few different objects
# More specifically, rasterio has a CRS() class that subclasses UserDict()
# In Python 2 UserDict() is in its own module and does not subclass Mapping()
DICT_TYPES = (dict, collections.Mapping, UserDict)
