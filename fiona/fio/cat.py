"""$ fio cat"""


import json
import logging
import warnings

import click
import cligj

import fiona
from fiona.transform import transform_geom
from fiona.fio import options


warnings.simplefilter('default')


# Cat command
@click.command(short_help="Concatenate and print the features of datasets")
@cligj.files_in_arg
@cligj.precision_opt
@cligj.indent_opt
@cligj.compact_opt
@click.option('--ignore-errors/--no-ignore-errors', default=False,
              help="log errors but do not stop serialization.")
@options.dst_crs_opt
@cligj.use_rs_opt
@click.option('--bbox', default=None, metavar="w,s,e,n",
              help="filter for features intersecting a bounding box")
@click.pass_context
def cat(ctx, files, precision, indent, compact, ignore_errors, dst_crs,
        use_rs, bbox):
    """Concatenate and print the features of input datasets as a
    sequence of GeoJSON features."""
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')

    dump_kwds = {'sort_keys': True}
    if indent:
        dump_kwds['indent'] = indent
    if compact:
        dump_kwds['separators'] = (',', ':')
    item_sep = compact and ',' or ', '

    try:
        with fiona.drivers(CPL_DEBUG=verbosity>2):
            for path in files:
                with fiona.open(path) as src:
                    if bbox:
                        try:
                            bbox = tuple(map(float, bbox.split(',')))
                        except ValueError:
                            bbox = json.loads(bbox)
                    for i, feat in src.items(bbox=bbox):
                        if dst_crs or precision > 0:
                            g = transform_geom(
                                    src.crs, dst_crs, feat['geometry'],
                                    antimeridian_cutting=True,
                                    precision=precision)
                            feat['geometry'] = g
                            feat['bbox'] = fiona.bounds(g)
                        if use_rs:
                            click.echo(u'\u001e', nl=False)
                        click.echo(json.dumps(feat, **dump_kwds))

    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()
