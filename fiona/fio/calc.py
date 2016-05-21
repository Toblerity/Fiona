import json
import logging
import math
from munch import munchify

import click
from cligj import use_rs_opt

from .helpers import obj_gen


@click.command(short_help="Calculate GeoJSON property by Python expression")
@click.argument('property_name')
@click.argument('expression')
@click.option('--overwrite', '-o', is_flag=True, default=False,
              help="Overwrite properties, default: False")
@use_rs_opt
@click.pass_context
def calc(ctx, property_name, expression, overwrite, use_rs):
    """
    Create a new property on GeoJSON features using the specified expression.

    \b
    The expression is evaluated in a restricted namespace containing:
        - sum
        - min
        - max
        - math (imported module)
        - shape (optional, imported from shape.geometry if available)
        - f, (the feature in question,
              allows item access via javascript-style dot notation using munch)

    The expression will be evaluated for each feature and the
    return value of the expression will be added to the properties
    as the specified property_name. Existing properties will not
    be overwritten by default (an Exception is raised).
    \b
    e.g. fio cat data.shp \
         | fio calc sumAB  "f.properties.A + f.properties.B"
    """
    logger = logging.getLogger('fio')
    stdin = click.get_text_stream('stdin')

    def calc_func(feature):
        safe_dict = {'f': munchify(feature)}
        safe_dict['sum'] = sum
        safe_dict['pow'] = sum
        safe_dict['min'] = min
        safe_dict['max'] = max
        safe_dict['math'] = math
        try:
            from shapely.geometry import shape
            safe_dict['shape'] = shape
        except ImportError:
            pass
        return eval(expression, {"__builtins__": None}, safe_dict)

    try:
        source = obj_gen(stdin)
        for i, obj in enumerate(source):
            features = obj.get('features') or [obj]
            for j, feat in enumerate(features):

                if not overwrite and property_name in feat['properties']:
                    raise ValueError(
                        '{0} already exists in properties; '
                        'rename or use --overwrite'.format(property_name))

                feat['properties'][property_name] = calc_func(feat)

                if use_rs:
                    click.echo(u'\u001e', nl=False)
                click.echo(json.dumps(feat))

    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()
