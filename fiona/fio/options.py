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


def cb_multilayer(ctx, param, value):
    """
    Transform layer options from strings ("1:a,1:b", "2:a,2:c,2:z") to
    {
    '1': ['a', 'b'],
    '2': ['a', 'c', 'z']
    }
    """
    out = defaultdict(list)
    for raw in value:
        for v in raw.split(','):
            ds, name = v.split(':')
            out[ds].append(name)
    return out


def validate_multilayer_file_index(files, layerdict):
    """
    Ensure file indexes provided in the --layer option are valid
    """
    for key in layerdict.keys():
        if key not in [str(k) for k in range(1, len(files) + 1)]:
            layer = key + ":" + layerdict[key][0]
            raise click.BadParameter("Layer {} does not exist".format(layer))
