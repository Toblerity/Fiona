"""Common commandline options for `fio`"""


from collections import defaultdict

import click


src_crs_opt = click.option('--src-crs', '--src_crs', help="Source CRS.")
dst_crs_opt = click.option('--dst-crs', '--dst_crs', help="Destination CRS.")


def cb_layer(ctx, param, value):
    """Let --layer be a name or index."""
    if value is None or not value.isdigit():
        return value
    else:
        return int(value)


def cb_multi_layer(ctx, param, value):
    """
    Transform layer options from strings ("1.a,1.b", "2.a,2.c,2.z") to
    {
    '1': ['a', 'b'],
    '2': ['a', 'c', 'z']
    }
    """
    out = defaultdict(list)
    for raw in value:
        for v in raw.split(','):
            ds, name = v.split('.')
            out[ds].append(name)
    return out
