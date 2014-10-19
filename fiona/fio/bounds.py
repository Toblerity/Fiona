import json
import logging
import sys

import click

import fiona
from fiona.fio.cli import cli, obj_gen


# Bounds command
@cli.command(short_help="Print the extent of GeoJSON objects")
@click.option('--precision', type=int, default=-1, metavar="N",
              help="Decimal precision of coordinates.")
@click.option('--explode/--no-explode', default=False,
              help="Explode collections into features (default: no).")
@click.option('--with-id/--without-id', default=False,
              help="Print GeoJSON ids and bounding boxes together "
                   "(default: without).")
@click.option('--with-obj/--without-obj', default=False,
              help="Print GeoJSON objects and bounding boxes together "
                   "(default: without).")
@click.option('--x-json-seq-rs/--x-json-seq-no-rs', default=False,
              help="Use RS as text separator instead of LF. "
                   "Experimental (default: no).")
@click.pass_context
def bounds(ctx, precision, explode, with_id, with_obj, x_json_seq_rs):
    """Print the bounding boxes of GeoJSON objects read from stdin.
    
    Optionally explode collections and print the bounds of their
    features.

    To print identifiers for input objects along with their bounds
    as a {id: identifier, bbox: bounds} JSON object, use --with-id.

    To print the input objects themselves along with their bounds
    as GeoJSON object, use --with-obj. This has the effect of updating
    input objects with {id: identifier, bbox: bounds}.
    """
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    stdin = click.get_text_stream('stdin')
    stdout = click.get_text_stream('stdout')
    try:
        source = obj_gen(stdin)
        for i, obj in enumerate(source):
            obj_id = obj.get('id', 'collection:' + str(i))
            xs = []
            ys = []
            features = obj.get('features') or [obj]
            for j, feat in enumerate(features):
                feat_id = feat.get('id', 'feature:' + str(i))
                w, s, e, n = fiona.bounds(feat)
                if precision > 0:
                    w, s, e, n = (round(v, precision) 
                                  for v in (w, s, e, n))
                if explode:
                    if with_id:
                        rec = {'parent': obj_id, 'id': feat_id, 'bbox': (w, s, e, n)}
                    elif with_obj:
                        feat.update(parent=obj_id, bbox=(w, s, e, n))
                        rec = feat
                    else:
                        rec = (w, s, e, n)
                    stdout.write(json.dumps(rec))
                    stdout.write('\n')
                else:
                    xs.extend([w, e])
                    ys.extend([s, n])
            if not explode:
                w, s, e, n = (min(xs), min(ys), max(xs), max(ys))
                if with_id:
                    rec = {'id': obj_id, 'bbox': (w, s, e, n)}
                elif with_obj:
                    obj.update(id=obj_id, bbox=(w, s, e, n))
                    rec = obj
                else:
                    rec = (w, s, e, n)
                stdout.write(json.dumps(rec))
                stdout.write('\n')

        sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)
