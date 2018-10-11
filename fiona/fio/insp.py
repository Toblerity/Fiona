"""$ fio insp"""


import code
import logging
import sys

import click

import fiona
from fiona.fio import with_context_env


@click.command(short_help="Open a dataset and start an interpreter.")
@click.argument('src_path', required=True)
@click.option('--ipython', 'interpreter', flag_value='ipython',
              help="Use IPython as interpreter.")
@click.pass_context
@with_context_env
def insp(ctx, src_path, interpreter):
    """Open a collection within an interactive interpreter.
    """
    logger = logging.getLogger(__name__)
    banner = 'Fiona %s Interactive Inspector (Python %s)\n' \
             'Type "src.schema", "next(src)", or "help(src)" ' \
             'for more information.' \
             % (fiona.__version__, '.'.join(map(str, sys.version_info[:3])))

    try:
        with fiona.open(src_path) as src:
            scope = locals()
            if not interpreter:
                code.interact(banner, local=scope)
            elif interpreter == 'ipython':
                import IPython
                IPython.InteractiveShell.banner1 = banner
                IPython.start_ipython(argv=[], user_ns=scope)
            else:
                raise click.ClickException(
                    'Interpreter {} is unsupported or missing '
                    'dependencies'.format(interpreter))

    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()
