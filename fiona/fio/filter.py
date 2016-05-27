"""$ fio filter"""


import json
import logging

import click
from cligj import use_rs_opt

from fiona.fio.helpers import obj_gen, eval_feature_expression


@click.command()
@click.argument('filter_expression')
@use_rs_opt
@click.pass_context
def filter(ctx, filter_expression, use_rs):
    """
    Filter GeoJSON features by python expression.

    Features are read from stdin.

    The expression is evaluated in a restricted namespace containing:
        - sum, pow, min, max and the imported math module
        - shape (optional, imported from shapely.geometry if available)
        - bool, int, str, len, float type conversions
        - f (the feature to be evaluated,
             allows item access via javascript-style dot notation using munch)

    The expression will be evaluated for each feature and, if true,
    the feature will be included in the output.

    e.g. fio cat data.shp \
         | fio filter "f.properties.area > 1000.0" \
         | fio collect > large_polygons.geojson
    """

    logger = logging.getLogger('fio')
    stdin = click.get_text_stream('stdin')

    try:
        source = obj_gen(stdin)
        for i, obj in enumerate(source):
            features = obj.get('features') or [obj]
            for j, feat in enumerate(features):
                if not eval_feature_expression(feat, filter_expression):
                    continue

                if use_rs:
                    click.echo(u'\u001e', nl=False)
                click.echo(json.dumps(feat))

    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()
