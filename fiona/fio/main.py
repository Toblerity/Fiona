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


@with_plugins(ep for ep in list(iter_entry_points('fiona.fio_commands')) +
              list(iter_entry_points('fiona.fio_plugins')))
@click.group()
@verbose_opt
@quiet_opt
@click.version_option(fio_version)
@click.pass_context
def main_group(ctx, verbose, quiet):

    """Fiona command line interface."""

    verbosity = verbose - quiet
    configure_logging(verbosity)
    ctx.obj = {'verbosity': verbosity}
