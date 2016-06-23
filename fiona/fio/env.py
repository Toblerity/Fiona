"""$ fio env"""


import logging

import click

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
