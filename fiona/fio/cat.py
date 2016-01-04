from functools import partial
import itertools
import json
import logging
import sys
import warnings

import click
from cligj import (
    compact_opt, files_in_arg, indent_opt,
    sequence_opt, precision_opt, use_rs_opt)

import fiona
from fiona.transform import transform_geom
from .helpers import obj_gen
from . import options


FIELD_TYPES_MAP_REV = dict([(v, k) for k, v in fiona.FIELD_TYPES_MAP.items()])

warnings.simplefilter('default')


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
@click.command(short_help="Concatenate and print the features of datasets")
@files_in_arg
@precision_opt
@indent_opt
@compact_opt
@click.option('--ignore-errors/--no-ignore-errors', default=False,
              help="log errors but do not stop serialization.")
@options.dst_crs_opt
@use_rs_opt
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


# Collect command
@click.command(short_help="Collect a sequence of features.")
@precision_opt
@indent_opt
@compact_opt
@click.option('--record-buffered/--no-record-buffered', default=False,
              help="Economical buffering of writes at record, not collection "
              "(default), level.")
@click.option('--ignore-errors/--no-ignore-errors', default=False,
              help="log errors but do not stop serialization.")
@options.src_crs_opt
@click.option('--with-ld-context/--without-ld-context', default=False,
              help="add a JSON-LD context to JSON output.")
@click.option('--add-ld-context-item', multiple=True,
              help="map a term to a URI and add it to the output's JSON LD context.")
@click.option('--parse/--no-parse', default=True,
              help="load and dump the geojson feature (default is True)")
@click.pass_context
def collect(ctx, precision, indent, compact, record_buffered, ignore_errors,
            src_crs, with_ld_context, add_ld_context_item, parse):
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
        if not parse:
            raise click.UsageError("Can't specify --src-crs with --no-parse")
        transformer = partial(transform_geom, src_crs, 'EPSG:4326',
                              antimeridian_cutting=True, precision=precision)
    else:
        transformer = lambda x: x

    first_line = next(stdin)

    # If parsing geojson
    if parse:
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

    # If *not* parsing geojson
    else:
        # If input is RS-delimited JSON sequence.
        if first_line.startswith(u'\x1e'):
            def feature_gen():
                buffer = first_line.strip(u'\x1e')
                for line in stdin:
                    if line.startswith(u'\x1e'):
                        if buffer:
                            yield buffer
                        buffer = line.strip(u'\x1e')
                    else:
                        buffer += line
                else:
                    yield buffer
        else:
            def feature_gen():
                yield first_line
                for line in stdin:
                    yield line

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
                if parse:
                    sink.write(
                        json.dumps(first, **dump_kwds
                            ).replace("\n", rec_indent))
                else:
                    sink.write(first.replace("\n", rec_indent))
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
                    if parse:
                        sink.write(
                            json.dumps(rec, **dump_kwds
                                ).replace("\n", rec_indent))
                    else:
                        sink.write(rec.replace("\n", rec_indent))
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
            if parse:
                collection = {'type': 'FeatureCollection'}
                if with_ld_context:
                    collection['@context'] = make_ld_context(
                        add_ld_context_item)
                    collection['features'] = [
                        id_record(rec) for rec in source]
                else:
                    collection['features'] = list(source)
                json.dump(collection, sink, **dump_kwds)
            else:
                collection = {
                    'type': 'FeatureCollection',
                    'features': []}
                if with_ld_context:
                    collection['@context'] = make_ld_context(
                        add_ld_context_item)

                head, tail = json.dumps(collection, **dump_kwds).split('[]')
                sink.write(head)
                sink.write("[")
                sink.write(",".join(source))
                sink.write("]")
                sink.write(tail)
                sink.write("\n")

    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()


# Distribute command
@click.command(short_help="Distribute features from a collection")
@use_rs_opt
@click.pass_context
def distrib(ctx, use_rs):
    """Print the features of GeoJSON objects read from stdin.
    """
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    stdin = click.get_text_stream('stdin')
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
                if use_rs:
                    click.echo(u'\u001e', nl=False)
                click.echo(json.dumps(feat))
    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()


# Dump command
@click.command(short_help="Dump a dataset to GeoJSON.")
@click.argument('input', type=click.Path(), required=True)
@click.option('--encoding', help="Specify encoding of the input file.")
@precision_opt
@indent_opt
@compact_opt
@click.option('--record-buffered/--no-record-buffered', default=False,
    help="Economical buffering of writes at record, not collection "
         "(default), level.")
@click.option('--ignore-errors/--no-ignore-errors', default=False,
              help="log errors but do not stop serialization.")
@click.option('--with-ld-context/--without-ld-context', default=False,
        help="add a JSON-LD context to JSON output.")

@click.option('--add-ld-context-item', multiple=True,
        help="map a term to a URI and add it to the output's JSON LD context.")
@click.pass_context
def dump(ctx, input, encoding, precision, indent, compact, record_buffered,
         ignore_errors, with_ld_context, add_ld_context_item):
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

                if record_buffered:
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

    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()


# Load command.
@click.command(short_help="Load GeoJSON to a dataset in another format.")
@click.argument('output', type=click.Path(), required=True)
@click.option('-f', '--format', '--driver', required=True,
              help="Output format driver name.")
@options.src_crs_opt
@click.option(
    '--dst-crs', '--dst_crs',
    help="Destination CRS.  Defaults to --src-crs when not given.")
@click.option(
    '--sequence / --no-sequence', default=False,
    help="Specify whether the input stream is a LF-delimited sequence of GeoJSON "
         "features (the default) or a single GeoJSON feature collection.")
@click.pass_context
def load(ctx, output, driver, src_crs, dst_crs, sequence):
    """Load features from JSON to a file in another format.

    The input is a GeoJSON feature collection or optionally a sequence of
    GeoJSON feature objects."""
    verbosity = (ctx.obj and ctx.obj['verbosity']) or 2
    logger = logging.getLogger('fio')
    stdin = click.get_text_stream('stdin')

    dst_crs = dst_crs or src_crs

    if src_crs and dst_crs and src_crs != dst_crs:
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
    elif sequence:
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

    except Exception:
        logger.exception("Exception caught during processing")
        raise click.Abort()
