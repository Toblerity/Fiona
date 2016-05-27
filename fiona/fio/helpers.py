"""
Helper objects needed by multiple CLI commands.
"""
from functools import partial
import json
import math
import warnings

from munch import munchify


warnings.simplefilter('default')


def obj_gen(lines):
    """Return a generator of JSON objects loaded from ``lines``."""
    first_line = next(lines)
    if first_line.startswith(u'\x1e'):
        def gen():
            buffer = first_line.strip(u'\x1e')
            for line in lines:
                if line.startswith(u'\x1e'):
                    if buffer:
                        yield json.loads(buffer)
                    buffer = line.strip(u'\x1e')
                else:
                    buffer += line
            else:
                yield json.loads(buffer)
    else:
        def gen():
            yield json.loads(first_line)
            for line in lines:
                yield json.loads(line)
    return gen()


def nullable(val, cast):
    if val is None:
        return None
    else:
        return cast(val)


def eval_feature_expression(feature, expression):
    safe_dict = {'f': munchify(feature)}
    safe_dict.update({
        'sum': sum,
        'pow': pow,
        'min': min,
        'max': max,
        'math': math,
        'bool': bool,
        'int': partial(nullable, int),
        'str': partial(nullable, str),
        'float': partial(nullable, float),
        'len': partial(nullable, len),
    })
    try:
        from shapely.geometry import shape
        safe_dict['shape'] = shape
    except ImportError:
        pass
    return eval(expression, {"__builtins__": None}, safe_dict)
