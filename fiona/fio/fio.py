#!/usr/bin/env python

"""Fiona command line interface"""

import code
from functools import partial
import itertools
import json
import logging
import pprint
import sys
import warnings

import click
import six.moves

import fiona
import fiona.crs
from fiona.transform import transform_geom
from fiona.fio.cli import cli
from fiona.fio.cat import cat, collect, dump, distrib
from fiona.fio.bounds import bounds


FIELD_TYPES_MAP_REV = dict([(v, k) for k, v in fiona.FIELD_TYPES_MAP.items()])

warnings.simplefilter('default')

# Commands are below.

@cli.command(short_help="Print information about the fio environment.")
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
@cli.command(short_help="Print information about a dataset.")
# One or more files.
@click.argument('input', type=click.Path(exists=True))
@click.option('--indent', default=None, type=int, 
              help="Indentation level for pretty printed output.")
# Options to pick out a single metadata item and print it as
# a string.
@click.option('--count', 'meta_member', flag_value='count',
              help="Print the count of features.")
@click.option('-f', '--format', '--driver', 'meta_member', flag_value='driver',
              help="Print the format driver.")
@click.option('--crs', 'meta_member', flag_value='crs',
              help="Print the CRS as a PROJ.4 string.")
@click.option('--bounds', 'meta_member', flag_value='bounds',
              help="Print the nodata value.")
@click.pass_context
def info(ctx, input, indent, meta_member):
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('rio')

    stdout = click.get_text_stream('stdout')
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
                    stdout.write(json.dumps(info, indent=indent))
                    stdout.write("\n")
        sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)

# Insp command.
@cli.command(short_help="Open a dataset and start an interpreter.")
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


# Load command.
@cli.command(short_help="Load GeoJSON to a dataset in another format.")
@click.argument('output', type=click.Path(), required=True)
@click.option('-f', '--format', '--driver', required=True,
              help="Output format driver name.")
@click.option('--src_crs', default=None, help="Source CRS.")
@click.option('--dst_crs', default=None, help="Destination CRS.")
@click.option('--x-json-seq/--x-json-obj', default=False,
              help="Read a LF-delimited JSON sequence (default is object). Experimental.")
@click.pass_context

def load(ctx, output, driver, src_crs, dst_crs, x_json_seq):
    """Load features from JSON to a file in another format.

    The input is a GeoJSON feature collection or optionally a sequence of
    GeoJSON feature objects."""
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    stdin = click.get_text_stream('stdin')

    if src_crs and dst_crs:
        transformer = partial(transform_geom, src_crs, dst_crs,
                              antimeridian_cutting=True, precision=-1)
    else:
        transformer = lambda x: x

    first_line = next(stdin)

    # If input is RS-delimited JSON sequence.
    if first_line.startswith(u'\x1e'):
        def feature_gen():
            buffer = first_line.strip(u'\x1e')
            for line in stdin:
                if line.startswith(u'\x1e'):
                    if buffer:
                        feat = json.loads(buffer)
                        feat['geometry'] = transformer(feat['geometry'])
                        yield feat
                    buffer = line.strip(u'\x1e')
                else:
                    buffer += line
            else:
                feat = json.loads(buffer)
                feat['geometry'] = transformer(feat['geometry'])
                yield feat
    elif x_json_seq:
        def feature_gen():
            yield json.loads(first_line)
            for line in stdin:
                feat = json.loads(line)
                feat['geometry'] = transformer(feat['geometry'])
                yield feat
    else:
        def feature_gen():
            text = "".join(itertools.chain([first_line], stdin))
            for feat in json.loads(text)['features']:
                feat['geometry'] = transformer(feat['geometry'])
                yield feat

    try:
        source = feature_gen()

        # Use schema of first feature as a template.
        # TODO: schema specified on command line?
        first = next(source)
        schema = {'geometry': first['geometry']['type']}
        schema['properties'] = dict([
            (k, FIELD_TYPES_MAP_REV.get(type(v)) or 'str')
            for k, v in first['properties'].items()])

        with fiona.drivers(CPL_DEBUG=verbosity>2):
            with fiona.open(
                    output, 'w',
                    driver=driver,
                    crs=dst_crs,
                    schema=schema) as dst:
                dst.write(first)
                dst.writerecords(source)
        sys.exit(0)
    except IOError:
        logger.info("IOError caught")
        sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)


if __name__ == '__main__':
    cli()
