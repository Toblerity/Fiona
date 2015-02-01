from functools import partial
import json
import logging
import sys

import click

import fiona
from fiona.transform import transform_geom
from fiona.fio.cli import cli, obj_gen


def make_ld_context(context_items):
    """Returns a JSON-LD Context object.

    See http://json-ld.org/spec/latest/json-ld."""
    ctx = {
      "@context": {
        "geojson": "http://ld.geojson.org/vocab#",
        "Feature": "geojson:Feature",
        "FeatureCollection": "geojson:FeatureCollection",
        "GeometryCollection": "geojson:GeometryCollection",
        "LineString": "geojson:LineString",
        "MultiLineString": "geojson:MultiLineString",
        "MultiPoint": "geojson:MultiPoint",
        "MultiPolygon": "geojson:MultiPolygon",
        "Point": "geojson:Point",
        "Polygon": "geojson:Polygon",
        "bbox": {
          "@container": "@list",
          "@id": "geojson:bbox"
        },
        "coordinates": "geojson:coordinates",
        "datetime": "http://www.w3.org/2006/time#inXSDDateTime",
        "description": "http://purl.org/dc/terms/description",
        "features": {
          "@container": "@set",
          "@id": "geojson:features"
        },
        "geometry": "geojson:geometry",
        "id": "@id",
        "properties": "geojson:properties",
        "start": "http://www.w3.org/2006/time#hasBeginning",
        "stop": "http://www.w3.org/2006/time#hasEnding",
        "title": "http://purl.org/dc/terms/title",
        "type": "@type",
        "when": "geojson:when"
      }
    }
    for item in context_items or []:
        t, uri = item.split("=")
        ctx[t.strip()] = uri.strip()
    return ctx


def id_record(rec):
    """Converts a record's id to a blank node id and returns the record."""
    rec['id'] = '_:f%s' % rec['id']
    return rec


# Cat command
@cli.command(short_help="Concatenate and print the features of datasets")
# One or more files.
@click.argument('input', nargs=-1, type=click.Path(exists=True))
# Coordinate precision option.
@click.option('--precision', type=int, default=-1, metavar="N",
              help="Decimal precision of coordinates.")
@click.option('--indent', default=None, type=int, metavar="N",
              help="Indentation level for pretty printed output.")
@click.option('--compact/--no-compact', default=False,
              help="Use compact separators (',', ':').")
@click.option('--ignore-errors/--no-ignore-errors', default=False,
              help="log errors but do not stop serialization.")
@click.option('--dst_crs', default=None, metavar="EPSG:NNNN",
              help="Destination CRS.")
# Use ASCII RS control code to signal a sequence item (False is default).
# See http://tools.ietf.org/html/draft-ietf-json-text-sequence-05.
# Experimental.
@click.option('--x-json-seq-rs/--x-json-seq-no-rs', default=True,
        help="Use RS as text separator instead of LF. Experimental.")
@click.option('--bbox', default=None, metavar="w,s,e,n",
              help="filter for features intersecting a bounding box")
@click.pass_context
def cat(ctx, input, precision, indent, compact, ignore_errors, dst_crs,
        x_json_seq_rs, bbox):
    """Concatenate and print the features of input datasets as a
    sequence of GeoJSON features."""
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    sink = click.get_text_stream('stdout')

    dump_kwds = {'sort_keys': True}
    if indent:
        dump_kwds['indent'] = indent
    if compact:
        dump_kwds['separators'] = (',', ':')
    item_sep = compact and ',' or ', '

    try:
        with fiona.drivers(CPL_DEBUG=verbosity>2):
            for path in input:
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
                        if x_json_seq_rs:
                            sink.write(u'\u001e')
                        json.dump(feat, sink, **dump_kwds)
                        sink.write("\n")
        sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)


# Collect command
@cli.command(short_help="Collect a sequence of features.")
# Coordinate precision option.
@click.option('--precision', type=int, default=-1, metavar="N",
              help="Decimal precision of coordinates.")
@click.option('--indent', default=None, type=int, metavar="N",
              help="Indentation level for pretty printed output.")
@click.option('--compact/--no-compact', default=False,
              help="Use compact separators (',', ':').")
@click.option('--record-buffered/--no-record-buffered', default=False,
              help="Economical buffering of writes at record, not collection "
              "(default), level.")
@click.option('--ignore-errors/--no-ignore-errors', default=False,
              help="log errors but do not stop serialization.")
@click.option('--src_crs', default=None, metavar="EPSG:NNNN",
              help="Source CRS.")
@click.option('--with-ld-context/--without-ld-context', default=False,
              help="add a JSON-LD context to JSON output.")
@click.option('--add-ld-context-item', multiple=True,
              help="map a term to a URI and add it to the output's JSON LD context.")
@click.pass_context
def collect(ctx, precision, indent, compact, record_buffered, ignore_errors,
            src_crs, with_ld_context, add_ld_context_item):
    """Make a GeoJSON feature collection from a sequence of GeoJSON
    features and print it."""
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    stdin = click.get_text_stream('stdin')
    sink = click.get_text_stream('stdout')

    dump_kwds = {'sort_keys': True}
    if indent:
        dump_kwds['indent'] = indent
    if compact:
        dump_kwds['separators'] = (',', ':')
    item_sep = compact and ',' or ', '

    if src_crs:
        transformer = partial(transform_geom, src_crs, 'EPSG:4326',
                              antimeridian_cutting=True, precision=precision)
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
    else:
        def feature_gen():
            feat = json.loads(first_line)
            feat['geometry'] = transformer(feat['geometry'])
            yield feat
            for line in stdin:
                feat = json.loads(line)
                feat['geometry'] = transformer(feat['geometry'])
                yield feat

    try:
        source = feature_gen()

        if record_buffered:
            # Buffer GeoJSON data at the feature level for smaller
            # memory footprint.
            indented = bool(indent)
            rec_indent = "\n" + " " * (2 * (indent or 0))

            collection = {
                'type': 'FeatureCollection',
                'features': [] }
            if with_ld_context:
                collection['@context'] = make_ld_context(
                    add_ld_context_item)

            head, tail = json.dumps(collection, **dump_kwds).split('[]')

            sink.write(head)
            sink.write("[")

            # Try the first record.
            try:
                i, first = 0, next(source)
                if with_ld_context:
                    first = id_record(first)
                if indented:
                    sink.write(rec_indent)
                sink.write(
                    json.dumps(first, **dump_kwds
                        ).replace("\n", rec_indent))
            except StopIteration:
                pass
            except Exception as exc:
                # Ignoring errors is *not* the default.
                if ignore_errors:
                    logger.error(
                        "failed to serialize file record %d (%s), "
                        "continuing",
                        i, exc)
                else:
                    # Log error and close up the GeoJSON, leaving it
                    # more or less valid no matter what happens above.
                    logger.critical(
                        "failed to serialize file record %d (%s), "
                        "quiting",
                        i, exc)
                    sink.write("]")
                    sink.write(tail)
                    if indented:
                        sink.write("\n")
                    raise

            # Because trailing commas aren't valid in JSON arrays
            # we'll write the item separator before each of the
            # remaining features.
            for i, rec in enumerate(source, 1):
                try:
                    if with_ld_context:
                        rec = id_record(rec)
                    if indented:
                        sink.write(rec_indent)
                    sink.write(item_sep)
                    sink.write(
                        json.dumps(rec, **dump_kwds
                            ).replace("\n", rec_indent))
                except Exception as exc:
                    if ignore_errors:
                        logger.error(
                            "failed to serialize file record %d (%s), "
                            "continuing",
                            i, exc)
                    else:
                        logger.critical(
                            "failed to serialize file record %d (%s), "
                            "quiting",
                            i, exc)
                        sink.write("]")
                        sink.write(tail)
                        if indented:
                            sink.write("\n")
                        raise

            # Close up the GeoJSON after writing all features.
            sink.write("]")
            sink.write(tail)
            if indented:
                sink.write("\n")

        else:
            # Buffer GeoJSON data at the collection level. The default.
            collection = {'type': 'FeatureCollection'}
            if with_ld_context:
                collection['@context'] = make_ld_context(
                    add_ld_context_item)
                collection['features'] = [
                    id_record(rec) for rec in source]
            else:
                collection['features'] = list(source)
            json.dump(collection, sink, **dump_kwds)
            sink.write("\n")

        sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)


# Distribute command
@cli.command(short_help="Distribute features from a collection")
@click.option('--x-json-seq-rs/--x-json-seq-no-rs', default=False,
              help="Use RS as text separator instead of LF. "
                   "Experimental (default: no).")
@click.pass_context
def distrib(ctx, x_json_seq_rs):
    """Print the features of GeoJSON objects read from stdin.
    """
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    stdin = click.get_text_stream('stdin')
    stdout = click.get_text_stream('stdout')
    try:
        source = obj_gen(stdin)
        for i, obj in enumerate(source):
            obj_id = obj.get('id', 'collection:' + str(i))
            features = obj.get('features') or [obj]
            for j, feat in enumerate(features):
                if obj.get('type') == 'FeatureCollection':
                    feat['parent'] = obj_id
                feat_id = feat.get('id', 'feature:' + str(i))
                feat['id'] = feat_id
                stdout.write(json.dumps(feat))
                stdout.write('\n')
        sys.exit(0)
    except Exception:
        raise
        #logger.exception("Failed. Exception caught")
        #sys.exit(1)


# Dump command
@cli.command(short_help="Dump a dataset to GeoJSON.")
@click.argument('input', type=click.Path(), required=True)
@click.option('--encoding', help="Specify encoding of the input file.")
# Coordinate precision option.
@click.option('--precision', type=int, default=-1,
              help="Decimal precision of coordinates.")
@click.option('--indent', default=None, type=int,
              help="Indentation level for pretty printed output.")
@click.option('--compact/--no-compact', default=False,
              help="Use compact separators (',', ':').")
@click.option('--record-buffered/--no-record-buffered', default=False,
    help="Economical buffering of writes at record, not collection "
         "(default), level.")
@click.option('--ignore-errors/--no-ignore-errors', default=False,
              help="log errors but do not stop serialization.")
@click.option('--with-ld-context/--without-ld-context', default=False,
        help="add a JSON-LD context to JSON output.")

@click.option('--add-ld-context-item', multiple=True,
        help="map a term to a URI and add it to the output's JSON LD context.")
@click.option('--x-json-seq/--x-json-obj', default=False,
    help="Write a LF-delimited JSON sequence (default is object). "
         "Experimental.")
# Use ASCII RS control code to signal a sequence item (False is default).
# See http://tools.ietf.org/html/draft-ietf-json-text-sequence-05.
# Experimental.
@click.option('--x-json-seq-rs/--x-json-seq-no-rs', default=True,
        help="Use RS as text separator. Experimental.")
@click.pass_context
def dump(ctx, input, encoding, precision, indent, compact, record_buffered,
         ignore_errors, with_ld_context, add_ld_context_item,
         x_json_seq, x_json_seq_rs):
    """Dump a dataset either as a GeoJSON feature collection (the default)
    or a sequence of GeoJSON features."""
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    sink = click.get_text_stream('stdout')

    dump_kwds = {'sort_keys': True}
    if indent:
        dump_kwds['indent'] = indent
    if compact:
        dump_kwds['separators'] = (',', ':')
    item_sep = compact and ',' or ', '

    open_kwds = {}
    if encoding:
        open_kwds['encoding'] = encoding

    def transformer(crs, feat):
        tg = partial(transform_geom, crs, 'EPSG:4326',
                     antimeridian_cutting=True, precision=precision)
        feat['geometry'] = tg(feat['geometry'])
        return feat

    try:
        with fiona.drivers(CPL_DEBUG=verbosity>2):
            with fiona.open(input, **open_kwds) as source:
                meta = source.meta
                meta['fields'] = dict(source.schema['properties'].items())

                if x_json_seq:
                    for feat in source:
                        feat = transformer(source.crs, feat)
                        if x_json_seq_rs:
                            sink.write(u'\u001e')
                        json.dump(feat, sink, **dump_kwds)
                        sink.write("\n")

                elif record_buffered:
                    # Buffer GeoJSON data at the feature level for smaller
                    # memory footprint.
                    indented = bool(indent)
                    rec_indent = "\n" + " " * (2 * (indent or 0))

                    collection = {
                        'type': 'FeatureCollection',
                        'fiona:schema': meta['schema'],
                        'fiona:crs': meta['crs'],
                        'features': [] }
                    if with_ld_context:
                        collection['@context'] = make_ld_context(
                            add_ld_context_item)

                    head, tail = json.dumps(collection, **dump_kwds).split('[]')

                    sink.write(head)
                    sink.write("[")

                    itr = iter(source)

                    # Try the first record.
                    try:
                        i, first = 0, next(itr)
                        first = transformer(first)
                        if with_ld_context:
                            first = id_record(first)
                        if indented:
                            sink.write(rec_indent)
                        sink.write(
                            json.dumps(first, **dump_kwds
                                ).replace("\n", rec_indent))
                    except StopIteration:
                        pass
                    except Exception as exc:
                        # Ignoring errors is *not* the default.
                        if ignore_errors:
                            logger.error(
                                "failed to serialize file record %d (%s), "
                                "continuing",
                                i, exc)
                        else:
                            # Log error and close up the GeoJSON, leaving it
                            # more or less valid no matter what happens above.
                            logger.critical(
                                "failed to serialize file record %d (%s), "
                                "quiting",
                                i, exc)
                            sink.write("]")
                            sink.write(tail)
                            if indented:
                                sink.write("\n")
                            raise

                    # Because trailing commas aren't valid in JSON arrays
                    # we'll write the item separator before each of the
                    # remaining features.
                    for i, rec in enumerate(itr, 1):
                        rec = transformer(rec)
                        try:
                            if with_ld_context:
                                rec = id_record(rec)
                            if indented:
                                sink.write(rec_indent)
                            sink.write(item_sep)
                            sink.write(
                                json.dumps(rec, **dump_kwds
                                    ).replace("\n", rec_indent))
                        except Exception as exc:
                            if ignore_errors:
                                logger.error(
                                    "failed to serialize file record %d (%s), "
                                    "continuing",
                                    i, exc)
                            else:
                                logger.critical(
                                    "failed to serialize file record %d (%s), "
                                    "quiting",
                                    i, exc)
                                sink.write("]")
                                sink.write(tail)
                                if indented:
                                    sink.write("\n")
                                raise

                    # Close up the GeoJSON after writing all features.
                    sink.write("]")
                    sink.write(tail)
                    if indented:
                        sink.write("\n")

                else:
                    # Buffer GeoJSON data at the collection level. The default.
                    collection = {
                        'type': 'FeatureCollection',
                        'fiona:schema': meta['schema'],
                        'fiona:crs': meta['crs']}
                    if with_ld_context:
                        collection['@context'] = make_ld_context(
                            add_ld_context_item)
                        collection['features'] = [
                            id_record(transformer(rec)) for rec in source]
                    else:
                        collection['features'] = [transformer(source.crs, rec) for rec in source]
                    json.dump(collection, sink, **dump_kwds)

        sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)
