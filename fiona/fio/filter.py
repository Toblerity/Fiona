import json
import logging
import math

import click
from cligj import use_rs_opt

from .helpers import obj_gen


@click.command(short_help="Filter GeoJSON features by python expression")
@click.argument('filter')
@use_rs_opt
@click.pass_context
def filter(ctx, filter, use_rs):
    """
    Filter GeoJSON objects read from stdin against the specified expression.

    The expression is evaluated in a restricted namespace containing:
        - sum
        - min
        - max
        - math, imported module
        - f, the feature in question

    The expression will be evaluated for each feature and, if true,
    the feature will be included in the output.

    e.g. fio cat data.shp \
         | fio filter "f['properties']['area'] > 1000.0" \
         | fio collect > large_polygons.geojson
    """
    logger = logging.getLogger('fio')
    stdin = click.get_text_stream('stdin')

    def filter_func(feature):
        safe_dict = {'f': feature}
        safe_dict['sum'] = sum
        safe_dict['pow'] = sum
        safe_dict['min'] = min
        safe_dict['max'] = max
        safe_dict['math'] = math
        return eval(filter, {"__builtins__": None}, safe_dict)

    try:
        source = obj_gen(stdin)
        for i, obj in enumerate(source):
            features = obj.get('features') or [obj]
            for j, feat in enumerate(features):
                if not filter_func(feat):
                    continue

                if use_rs:
                    click.echo(u'\u001e', nl=False)
                click.echo(json.dumps(feat))

    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()
