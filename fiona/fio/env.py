"""$ fio env"""

import json
import logging

import click

import fiona
from fiona.fio import with_context_env


@click.command(short_help="Print information about the fio environment.")
@click.option('--formats', 'key', flag_value='formats', default=True,
              help="Enumerate the available formats.")
@click.option('--credentials', 'key', flag_value='credentials', default=False,
              help="Print credentials.")
@click.pass_context
def env(ctx, key):
    """Print information about the Fiona environment: available
    formats, etc.
    """
    stdout = click.get_text_stream('stdout')
    with ctx.obj['env'] as env:
        if key == 'formats':
            for k, v in sorted(fiona.supported_drivers.items()):
                modes = ', '.join("'" + m + "'" for m in v)
                stdout.write("%s (modes %s)\n" % (k, modes))
            stdout.write('\n')
        elif key == 'credentials':
            click.echo(json.dumps(env.session.credentials))
