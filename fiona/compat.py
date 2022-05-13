from collections import UserDict
from collections.abc import Mapping

# Users can pass in objects that subclass a few different objects
# More specifically, rasterio has a CRS() class that subclasses UserDict()
DICT_TYPES = (dict, Mapping, UserDict)


def strencode(instr, encoding="utf-8"):
    try:
        instr = instr.encode(encoding)
    except (UnicodeDecodeError, AttributeError):
        pass
    return instr
