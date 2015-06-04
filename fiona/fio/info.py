"""
Commands to get info about datasources and the Fiona environment
"""


import code
import logging
import json
import sys

import click
from cligj import indent_opt

import fiona


@click.command(short_help="Print information about the fio environment.")
@click.option('--formats', 'key', flag_value='formats', default=True,
              help="Enumerate the available formats.")
@click.pass_context
def env(ctx, key):
    """Print information about the Fiona environment: available
    formats, etc.
    """
    verbosity = (ctx.obj and ctx.obj.get('verbosity')) or 1
    logger = logging.getLogger('fio')
    stdout = click.get_text_stream('stdout')
    with fiona.drivers(CPL_DEBUG=(verbosity > 2)) as env:
        if key == 'formats':
            for k, v in sorted(fiona.supported_drivers.items()):
                modes = ', '.join("'" + m + "'" for m in v)
                stdout.write("%s (modes %s)\n" % (k, modes))
            stdout.write('\n')


# Info command.
@click.command(short_help="Print information about a dataset.")
# One or more files.
@click.argument('input', type=click.Path(exists=True))
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
@click.pass_context
def info(ctx, input, indent, meta_member):
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('rio')
    try:
        with fiona.drivers(CPL_DEBUG=verbosity>2):
            with fiona.open(input) as src:
                info = src.meta
                info.update(bounds=src.bounds, count=len(src))
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
        sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)


# Insp command.
@click.command(short_help="Open a dataset and start an interpreter.")
@click.argument('src_path', type=click.Path(exists=True))
@click.pass_context
def insp(ctx, src_path):
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    try:
        with fiona.drivers(CPL_DEBUG=verbosity>2):
            with fiona.open(src_path) as src:
                code.interact(
                    'Fiona %s Interactive Inspector (Python %s)\n'
                    'Type "src.schema", "next(src)", or "help(src)" '
                    'for more information.' %  (
                        fiona.__version__, '.'.join(
                            map(str, sys.version_info[:3]))),
                    local=locals())
            sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)
