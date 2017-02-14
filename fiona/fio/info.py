"""$ fio info"""


import logging
import json

import click
from cligj import indent_opt

import fiona
import fiona.crs
from fiona.fio import options


@click.command()
# One or more files.
@click.argument('input', type=click.Path(exists=False))
@click.option('--layer', metavar="INDEX|NAME", callback=options.cb_layer,
              help="Print information about a specific layer.  The first "
                   "layer is used by default.  Layers use zero-based "
                   "numbering when accessed by index.")
@indent_opt
# Options to pick out a single metadata item and print it as
# a string.
@click.option('--count', 'meta_member', flag_value='count',
              help="Print the count of features.")
@click.option('-f', '--format', '--driver', 'meta_member', flag_value='driver',
              help="Print the format driver.")
@click.option('--crs', 'meta_member', flag_value='crs',
              help="Print the CRS as a PROJ.4 string.")
@click.option('--bounds', 'meta_member', flag_value='bounds',
              help="Print the boundary coordinates "
                   "(left, bottom, right, top).")
@click.option('--name', 'meta_member', flag_value='name',
              help="Print the datasource's name.")
@click.pass_context
def info(ctx, input, indent, meta_member, layer):

    """
    Print information about a dataset.

    When working with a multi-layer dataset the first layer is used by default.
    Use the '--layer' option to select a different layer.
    """

    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    try:
        with fiona.drivers(CPL_DEBUG=verbosity > 2):
            with fiona.open(input, layer=layer) as src:
                info = src.meta
                info.update(bounds=src.bounds, name=src.name)
                try:
                    info.update(count=len(src))
                except TypeError:
                    info.update(count=None)
                    logger.debug("Setting 'count' to None/null - layer does "
                                 "not support counting")
                proj4 = fiona.crs.to_string(src.crs)
                if proj4.startswith('+init=epsg'):
                    proj4 = proj4.split('=')[1].upper()
                info['crs'] = proj4
                if meta_member:
                    if isinstance(info[meta_member], (list, tuple)):
                        click.echo(" ".join(map(str, info[meta_member])))
                    else:
                        click.echo(info[meta_member])
                else:
                    click.echo(json.dumps(info, indent=indent))

    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()
