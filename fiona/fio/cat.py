"""fio-cat"""

import json
import logging
import warnings

import click
import cligj

import fiona
from fiona.transform import transform_geom
from fiona.model import ObjectEncoder
from fiona.fio import options, with_context_env
from fiona.errors import AttributeFilterError

warnings.simplefilter('default')


# Cat command
@click.command(short_help="Concatenate and print the features of datasets")
@click.argument('files', nargs=-1, required=True, metavar="INPUTS...")
@click.option('--layer', default=None, multiple=True,
              callback=options.cb_multilayer,
              help="Input layer(s), specified as 'fileindex:layer` "
                   "For example, '1:foo,2:bar' will concatenate layer foo "
                   "from file 1 and layer bar from file 2")
@cligj.precision_opt
@cligj.indent_opt
@cligj.compact_opt
@click.option('--ignore-errors/--no-ignore-errors', default=False,
              help="log errors but do not stop serialization.")
@options.dst_crs_opt
@cligj.use_rs_opt
@click.option(
    "--bbox",
    default=None,
    metavar="w,s,e,n",
    help="filter for features intersecting a bounding box",
)
@click.option(
    "--where",
    default=None,
    help="attribute filter using SQL where clause",
)
@click.option(
    "--cut-at-antimeridian",
    is_flag=True,
    default=False,
    help="Optionally cut geometries at the anti-meridian. To be used only for a geographic destination CRS.",
)
@click.pass_context
@with_context_env
def cat(
    ctx,
    files,
    precision,
    indent,
    compact,
    ignore_errors,
    dst_crs,
    use_rs,
    bbox,
    where,
    cut_at_antimeridian,
    layer,
):
    """
    Concatenate and print the features of input datasets as a sequence of
    GeoJSON features.

    When working with a multi-layer dataset the first layer is used by default.
    Use the '--layer' option to select a different layer.

    """
    log = logging.getLogger(__name__)

    dump_kwds = {'sort_keys': True}
    if indent:
        dump_kwds['indent'] = indent
    if compact:
        dump_kwds['separators'] = (',', ':')

    # Validate file idexes provided in --layer option
    # (can't pass the files to option callback)
    if layer:
        options.validate_multilayer_file_index(files, layer)

    # first layer is the default
    for i in range(1, len(files) + 1):
        if str(i) not in layer.keys():
            layer[str(i)] = [0]

    try:
        if bbox:
            try:
                bbox = tuple(map(float, bbox.split(',')))
            except ValueError:
                bbox = json.loads(bbox)
        for i, path in enumerate(files, 1):
            for lyr in layer[str(i)]:
                with fiona.open(path, layer=lyr) as src:
                    for i, feat in src.items(bbox=bbox, where=where):
                        if dst_crs or precision >= 0:
                            g = transform_geom(
                                src.crs, dst_crs, feat['geometry'],
                                antimeridian_cutting=cut_at_antimeridian,
                                precision=precision)
                            feat['geometry'] = g
                            feat['bbox'] = fiona.bounds(g)
                        if use_rs:
                            click.echo('\x1e', nl=False)
                        click.echo(json.dumps(feat, cls=ObjectEncoder, **dump_kwds))

    except AttributeFilterError as e:
        raise click.BadParameter("'where' clause is invalid: " + str(e))
    except Exception:
        log.exception("Exception caught during processing")
        raise click.Abort()
