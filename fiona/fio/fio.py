#!/usr/bin/env python

"""Fiona command line interface"""

import code
import json
import logging
import pprint
import sys
import warnings

import click
import six.moves

import fiona
import fiona.crs

FIELD_TYPES_MAP_REV = {v: k for k, v in fiona.FIELD_TYPES_MAP.items()}

warnings.simplefilter('default')

def configure_logging(verbosity):
    log_level = max(10, 30 - 10*verbosity)
    logging.basicConfig(stream=sys.stderr, level=log_level)

# The CLI command group.
@click.group(help="Fiona command line interface.")
@click.option('--verbose', '-v', count=True, help="Increase verbosity.")
@click.option('--quiet', '-q', count=True, help="Decrease verbosity.")
@click.pass_context
def cli(ctx, verbose, quiet):
    verbosity = verbose - quiet
    configure_logging(verbosity)
    ctx.obj = {}
    ctx.obj['verbosity'] = verbosity

# Commands are below.

# Info command.
@cli.command(short_help="Print information about a data file.")
@click.argument('input', default='-', required=False)
@click.option('--indent', default=None, type=int,
              help="Indentation level for pretty printed output.")

# Options to pick out a single metadata item and print it as
# a string.
@click.option('--count', 'meta_member', flag_value='count',
              help="Print the count of features.")
@click.option('--driver', 'meta_member', flag_value='driver',
              help="Print the format driver.")
@click.option('--crs', 'meta_member', flag_value='crs',
              help="Print the CRS as a PROJ.4 string.")
@click.option('--bounds', 'meta_member', flag_value='bounds',
              help="Print the nodata value.")

@click.pass_context
def info(ctx, input, indent, meta_member):
    verbosity = ctx.obj['verbosity']
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
                        print(" ".join(map(str, info[meta_member])))
                    else:
                        print(info[meta_member])
                else:
                    stdout.write(json.dumps(info, indent=indent))
                    stdout.write("\n")
        sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)

# Insp command.
@cli.command(short_help="Open a data file and start an interpreter.")
@click.argument('src_path', type=click.Path(exists=True))
@click.pass_context
def insp(ctx, src_path):
    verbosity = ctx.obj['verbosity']
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

@click.option('--driver', required=True, help="Output format driver name.")

@click.option('--x-json-seq/--x-json-obj', default=False,
    help="Read a LF-delimited JSON sequence (default is object). Experimental.")

@click.pass_context

def load(ctx, output, driver, x_json_seq):
    """Load features from JSON to a file in another format.

    The input is a GeoJSON feature collection or optionally a sequence of
    GeoJSON feature objects."""
    verbosity = ctx.obj['verbosity']
    logger = logging.getLogger('fio')
    input = click.get_text_stream('stdin')

    try:
        if x_json_seq:
            feature_gen = six.moves.filter(
                lambda o: o.get('type') == 'Feature',
                (json.loads(text.strip()) for text in input))
        else:
            collection = json.load(input)
            feature_gen = iter(collection['features'])

        # Use schema of first feature as a template.
        # TODO: schema specified on command line?
        first = next(feature_gen)
        schema = {'geometry': first['geometry']['type']}
        schema['properties'] = {
            k: FIELD_TYPES_MAP_REV[type(v)]
            for k, v in first['properties'].items()}

        with fiona.drivers(CPL_DEBUG=verbosity>2):
            with fiona.open(
                    output, 'w',
                    driver=driver,
                    crs={'init': 'epsg:4326'},
                    schema=schema) as dst:
                dst.write(first)
                dst.writerecords(feature_gen)
        sys.exit(0)
    except IOError:
        logger.info("IOError caught")
        sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)


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


def round_rec(rec, precision=None):
    """Round coordinates of a geometric object to given precision."""
    if precision is None:
        return rec
    geom = rec['geometry']
    if geom['type'] == 'Point':
        x, y = geom['coordinates']
        xp, yp = [x], [y]
        if precision is not None:
            xp = [round(v, precision) for v in xp]
            yp = [round(v, precision) for v in yp]
        new_coords = tuple(zip(xp, yp))[0]
    if geom['type'] in ['LineString', 'MultiPoint']:
        xp, yp = zip(*geom['coordinates'])
        if precision is not None:
            xp = [round(v, precision) for v in xp]
            yp = [round(v, precision) for v in yp]
        new_coords = tuple(zip(xp, yp))
    elif geom['type'] in ['Polygon', 'MultiLineString']:
        new_coords = []
        for piece in geom['coordinates']:
            xp, yp = zip(*piece)
            if precision is not None:
                xp = [round(v, precision) for v in xp]
                yp = [round(v, precision) for v in yp]
            new_coords.append(tuple(zip(xp, yp)))
    elif geom['type'] == 'MultiPolygon':
        parts = geom['coordinates']
        new_coords = []
        for part in parts:
            inner_coords = []
            for ring in part:
                xp, yp = zip(*ring)
                if precision is not None:
                    xp = [round(v, precision) for v in xp]
                    yp = [round(v, precision) for v in yp]
                inner_coords.append(tuple(zip(xp, yp)))
            new_coords.append(inner_coords)
    rec['geometry'] = {'type': geom['type'], 'coordinates': new_coords}
    return rec


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
@click.option('--x-json-seq-rs/--x-json-seq-no-rs', default=False,
        help="Use RS as text separator. Experimental.")

@click.pass_context

def dump(ctx, input, encoding, precision, indent, compact, record_buffered,
         ignore_errors, with_ld_context, add_ld_context_item,
         x_json_seq, x_json_seq_rs):
    """Dump a dataset either as a GeoJSON feature collection (the default)
    or a sequence of GeoJSON features."""
    verbosity = ctx.obj['verbosity']
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

    try:
        with fiona.drivers(CPL_DEBUG=verbosity>2):
            with fiona.open(input, **open_kwds) as source:
                meta = source.meta
                meta['fields'] = dict(source.schema['properties'].items())

                if x_json_seq:
                    for feat in source:
                        if precision >= 0:
                            feat = round_rec(feat, precision)
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
                        if with_ld_context:
                            first = id_record(first)
                        if indented:
                            sink.write(rec_indent)
                        if precision >= 0:
                            first = round_rec(first, precision)
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
                        if precision >= 0:
                            rec = round_rec(rec, precision)
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
                        if precision >= 0:
                            collection['features'] = [
                                id_record(round_rec(rec, precision))
                                for rec in source]
                        else:
                            collection['features'] = [
                                id_record(rec) for rec in source]
                    else:
                        if precision >= 0:
                            collection['features'] = [
                                round_rec(rec, precision) for rec in source]
                        else:
                            collection['features'] = list(source)
                    json.dump(collection, sink, **dump_kwds)

        sys.exit(0)
    except Exception:
        logger.exception("Failed. Exception caught")
        sys.exit(1)


if __name__ == '__main__':
    cli()
