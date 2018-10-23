import sys
import collections

try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

if sys.version_info[0] >= 3:
    from urllib.parse import urlparse
    from collections import UserDict
    from inspect import getfullargspec as getargspec
else:
    from urlparse import urlparse
    from UserDict import UserDict
    from inspect import getargspec

if sys.version_info >= (3, 3):
    from collections.abc import Mapping
else:
    from collections import Mapping

# Users can pass in objects that subclass a few different objects
# More specifically, rasterio has a CRS() class that subclasses UserDict()
# In Python 2 UserDict() is in its own module and does not subclass Mapping()
DICT_TYPES = (dict, Mapping, UserDict)
