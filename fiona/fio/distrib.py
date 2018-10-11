"""$ fio distrib"""


import json
import logging

import click
import cligj

from fiona.fio import helpers, with_context_env


@click.command()
@cligj.use_rs_opt
@click.pass_context
@with_context_env
def distrib(ctx, use_rs):
    """Distribute features from a collection.

    Print the features of GeoJSON objects read from stdin.
    """
    logger = logging.getLogger(__name__)
    stdin = click.get_text_stream('stdin')
    try:
        source = helpers.obj_gen(stdin)
        for i, obj in enumerate(source):
            obj_id = obj.get('id', 'collection:' + str(i))
            features = obj.get('features') or [obj]
            for j, feat in enumerate(features):
                if obj.get('type') == 'FeatureCollection':
                    feat['parent'] = obj_id
                feat_id = feat.get('id', 'feature:' + str(i))
                feat['id'] = feat_id
                if use_rs:
                    click.echo(u'\u001e', nl=False)
                click.echo(json.dumps(feat))
    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()
