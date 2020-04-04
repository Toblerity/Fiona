"""$ fio env"""

import json
import os

import click

import fiona
import fiona._loading
with fiona._loading.add_gdal_dll_directories():
    from fiona._env import GDALDataFinder, PROJDataFinder


@click.command(short_help="Print information about the fio environment.")
@click.option('--formats', 'key', flag_value='formats', default=True,
              help="Enumerate the available formats.")
@click.option('--credentials', 'key', flag_value='credentials', default=False,
              help="Print credentials.")
@click.option('--gdal-data', 'key', flag_value='gdal_data', default=False,
              help="Print GDAL data path.")
@click.option('--proj-data', 'key', flag_value='proj_data', default=False,
              help="Print PROJ data path.")
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
        elif key == 'gdal_data':
            click.echo(os.environ.get('GDAL_DATA') or GDALDataFinder().search())
        elif key == 'proj_data':
            click.echo(os.environ.get('PROJ_LIB') or PROJDataFinder().search())
