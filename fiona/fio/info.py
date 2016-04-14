"""
Commands to get info about datasources and the Fiona environment
"""


import code
import logging
import json
import sys
import warnings

import click
from cligj import indent_opt

import fiona
import fiona.crs


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
@click.option('--name', 'meta_member', flag_value='name',
              help="Print the datasource's name.")
@click.pass_context
def info(ctx, input, indent, meta_member):
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    try:
        with fiona.drivers(CPL_DEBUG=verbosity>2):
            with fiona.open(input) as src:
                info = src.meta
                info.update(bounds=src.bounds, name=src.name)
                try:
                    info.update(count=len(src))
                except TypeError as e:
                    info.update(count=None)
                    msg = str(e) + "  Setting 'count' to 'null'"
                    warnings.warn(msg, RuntimeWarning)
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


# Insp command.
@click.command(short_help="Open a dataset and start an interpreter.")
@click.argument('src_path', type=click.Path(exists=True))
@click.option('--ipython', 'interpreter', flag_value='ipython',
              help="Use IPython as interpreter.")
@click.pass_context
def insp(ctx, src_path, interpreter):

    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')

    banner = 'Fiona %s Interactive Inspector (Python %s)\n' \
             'Type "src.schema", "next(src)", or "help(src)" ' \
             'for more information.' \
             % (fiona.__version__, '.'.join(map(str, sys.version_info[:3])))

    try:
        with fiona.drivers(CPL_DEBUG=verbosity > 2):
            with fiona.open(src_path) as src:

                scope = locals()

                if not interpreter:
                    code.interact(banner, local=scope)
                elif interpreter == 'ipython':
                    import IPython
                    IPython.InteractiveShell.banner1 = banner
                    IPython.start_ipython(argv=[], user_ns=scope)
                else:
                    raise click.ClickException('Interpreter %s is unsupported or missing '
                                               'dependencies' % interpreter)

    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()
