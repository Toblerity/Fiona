"""Common commandline options for `fio`"""


import click


src_crs_opt = click.option('--src-crs', '--src_crs', help="Source CRS.")
dst_crs_opt = click.option('--dst-crs', '--dst_crs', help="Destination CRS.")


def cb_layer(ctx, param, value):
    """Let --layer be a name or index."""

    if value is None or not value.isdigit():
        return value
    else:
        return int(value)
