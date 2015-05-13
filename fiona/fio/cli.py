"""Fiona's commandline interface core"""


import json
import logging
import os
import sys
import traceback
import warnings

import click
from cligj import verbose_opt, quiet_opt

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


class BrokenCommand(click.Command):

    """A dummy command that provides help for broken plugins."""

    def __init__(self, name):
        click.Command.__init__(self, name)
        self.help = (
            "Warning: entry point could not be loaded. Contact "
            "its author for help.\n\n\b\n"
            + traceback.format_exc())
        self.short_help = (
            "Warning: could not load plugin. See `fio %s --help`." % self.name)

    def invoke(self, ctx):

        """Print the error message instead of doing nothing."""

        click.echo(self.help, color=ctx.color)
        ctx.exit()


class FioGroup(click.Group):
    """Custom formatting for the commands of broken plugins."""

    def format_commands(self, ctx, formatter):
        """Extra format methods for multi methods that adds all the commands
        after the options.
        """

        rows = []
        for subcommand in self.list_commands(ctx):
            cmd = self.get_command(ctx, subcommand)
            # What is this, the tool lied about a command.  Ignore it
            if cmd is None:
                continue

            help = cmd.short_help or ''

            # Mark broken subcommands with a pile of poop.
            name = cmd.name
            if isinstance(cmd, BrokenCommand):
                if os.environ.get('FIO_HONESTLY'):
                    name += u'\U0001F4A9'
                else:
                    name += u'\u2020'

            rows.append((name, help))

        if rows:
            with formatter.section('Commands'):
                formatter.write_dl(rows)


# The CLI command group.
@click.group(help="Fiona command line interface.", cls=FioGroup)
@verbose_opt
@quiet_opt
@click.option('--version', is_flag=True, callback=print_version,
              expose_value=False, is_eager=True,
              help="Print Fiona version.")
@click.pass_context
def cli(ctx, verbose, quiet):
    verbosity = verbose - quiet
    configure_logging(verbosity)
    ctx.obj = {}
    ctx.obj['verbosity'] = verbosity


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
