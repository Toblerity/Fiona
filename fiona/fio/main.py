"""
Main click group for the CLI.  Needs to be isolated for entry-point loading.
"""


import logging
from pkg_resources import iter_entry_points
import warnings
import sys

import click
from click_plugins import with_plugins
from cligj import verbose_opt, quiet_opt

from fiona import __version__ as fio_version


def configure_logging(verbosity):
    log_level = max(10, 30 - 10*verbosity)
    logging.basicConfig(stream=sys.stderr, level=log_level)


def _cb_define(ctx, param, value):

    """
    Convert `name=val` arguments from the commandline to:

        {
            'name1': val,
            'another': val2
        }
    """

    out = {}
    for pair in value:
        try:
            name, value = pair.split('=')
            out[name] = value
        except ValueError:
            raise click.ClickException("Invalid syntax for 'name=val': {}".format(pair))
    return out


@with_plugins(list(iter_entry_points('fiona.fio_commands')) +
              list(iter_entry_points('fiona.fio_plugins')))
@click.group()
@click.option(
    '-D', 'define', multiple=True, metavar='NAME=VAL', callback=_cb_define,
    help="Define variables in the Fiona environment."
)
@verbose_opt
@quiet_opt
@click.version_option(fio_version)
@click.pass_context
def main_group(ctx, verbose, quiet, define):

    """Fiona command line interface."""

    verbosity = verbose - quiet
    configure_logging(verbosity)
    ctx.obj = {
        'verbosity': verbosity,
        'json_lib': __import__(define.get('json_lib', 'json'))
    }
