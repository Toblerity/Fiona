import logging
import sys
import warnings

import click

from fiona import __version__ as fio_version


warnings.simplefilter('default')

def configure_logging(verbosity):
    log_level = max(10, 30 - 10*verbosity)
    logging.basicConfig(stream=sys.stderr, level=log_level)


def print_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(fio_version)
    ctx.exit()


# The CLI command group.
@click.group(help="Fiona command line interface.")
@click.option('--verbose', '-v', count=True, help="Increase verbosity.")
@click.option('--quiet', '-q', count=True, help="Decrease verbosity.")
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help="Print Fiona version.")
@click.pass_context
def cli(ctx, verbose, quiet):
    verbosity = verbose - quiet
    configure_logging(verbosity)
    ctx.obj = {}
    ctx.obj['verbosity'] = verbosity
