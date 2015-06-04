"""
Helper objects needed by multiple CLI commands.
"""


import json
import warnings


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
