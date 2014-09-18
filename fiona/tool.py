""" fiona.tool

Converts Shapefiles (etc) to GeoJSON.
"""

import json
import logging
import pprint
import sys

from six.moves import map

import fiona


def open_output(arg):
    """Returns an opened output stream."""
    if arg == sys.stdout:
        return arg
    else:
        return open(arg, 'w')

def make_ld_context(context_items):
    """Returns a JSON-LD Context object. 
    
    See http://json-ld.org/spec/latest/json-ld."""
    ctx = {
        'type': '@type',
        'id': '@id',
        'FeatureCollection': '_:n1',
        '_crs': {'@id': '_:n2', '@type': '@id'},
        'bbox': 'http://geovocab.org/geometry#bbox',
        'features': '_:n3',
        'Feature': 'http://geovocab.org/spatial#Feature',
        'properties': '_:n4',
        'geometry': 'http://geovocab.org/geometry#geometry',
        'Point': 'http://geovocab.org/geometry#Point',
        'LineString': 'http://geovocab.org/geometry#LineString',
        'Polygon': 'http://geovocab.org/geometry#Polygon',
        'MultiPoint': 'http://geovocab.org/geometry#MultiPoint',
        'MultiLineString': 'http://geovocab.org/geometry#MultiLineString',
        'MultiPolygon': 'http://geovocab.org/geometry#MultiPolygon',
        'GeometryCollection': 
            'http://geovocab.org/geometry#GeometryCollection',
        'coordinates': '_:n5'}
    for item in context_items or []:
        t, uri = item.split("=")
        ctx[t.strip()] = uri.strip()
    return ctx

def crs_uri(crs):
    """Returns a CRS URN computed from a crs dict."""
    # References version 6.3 of the EPSG database.
    # TODO: get proper version from GDAL/OGR API?
    if crs['proj'] == 'longlat' and (
            crs['datum'] == 'WGS84' or crs['ellps'] == 'WGS84'):
        return 'urn:ogc:def:crs:OGC:1.3:CRS84'
    elif 'epsg:' in crs.get('init', ''):
        epsg, code = crs['init'].split(':')
        return 'urn:ogc:def:crs:EPSG::%s' % code
    else:
        return None

def id_record(rec):
    """Converts a record's id to a blank node id and returns the record."""
    rec['id'] = '_:f%s' % rec['id']
    return rec

def main(args, dump_kw, item_sep, ignore_errors):
    """Returns 0 on success, 1 on error, for sys.exit."""
    with fiona.drivers():
        
        with open_output(args.outfile) as sink:

            with fiona.open(args.infile) as source:

                meta = source.meta.copy()
                meta['fields'] = dict(source.schema['properties'].items())

                if args.description:
                    meta['name'] = args.infile
                    meta['schema']['properties'] = list(
                        source.schema['properties'].items())
                    json.dump(meta, sink, **dump_kw)
                
                elif args.record_buffered:
                    # Buffer GeoJSON data at the feature level for smaller
                    # memory footprint.

                    indented = bool(args.indent)
                    rec_indent = "\n" + " " * (2 * (args.indent or 0))

                    collection = {
                        'type': 'FeatureCollection',  
                        'fiona:schema': meta['schema'], 
                        'fiona:crs': meta['crs'],
                        '_crs': crs_uri(meta['crs']),
                        'features': [] }
                    if args.use_ld_context:
                        collection['@context'] = make_ld_context(
                            args.ld_context_items)
                    
                    head, tail = json.dumps(collection, **dump_kw).split('[]')
                    
                    sink.write(head)
                    sink.write("[")
                    
                    itr = iter(source)
                    
                    # Try the first record.
                    try:
                        i, first = 0, next(itr)
                        if args.use_ld_context:
                            first = id_record(first)
                        if indented:
                            sink.write(rec_indent)
                        sink.write(
                            json.dumps(first, **dump_kw
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
                            return 1
                    
                    # Because trailing commas aren't valid in JSON arrays
                    # we'll write the item separator before each of the
                    # remaining features.
                    for i, rec in enumerate(itr, 1):
                        try:
                            if args.use_ld_context:
                                rec = id_record(rec)
                            if indented:
                                sink.write(rec_indent)
                            sink.write(item_sep)
                            sink.write(
                                json.dumps(rec, **dump_kw
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
                                return 1
                    
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
                        'fiona:crs': meta['crs'],
                        '_crs': crs_uri(meta['crs']) }
                    if args.use_ld_context:
                        collection['@context'] = make_ld_context(
                            args.ld_context_items)
                        collection['features'] = list(map(id_record, source))
                    else:
                        collection['features'] = list(source)
                    json.dump(collection, sink, **dump_kw)

    return 0

if __name__ == '__main__':

    import argparse

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    logger = logging.getLogger('fiona.tool')

    parser = argparse.ArgumentParser(
        description="Serialize a file's records or description to GeoJSON")
    
    parser.add_argument('infile', 
        help="input file name")
    parser.add_argument('outfile',
        nargs='?', 
        help="output file name, defaults to stdout if omitted", 
        default=sys.stdout)
    parser.add_argument('-d', '--description',
        action='store_true', 
        help="serialize file's data description (schema) only")
    parser.add_argument('-n', '--indent', 
        type=int,
        default=None,
        metavar='N',
        help="indentation level in N number of chars")
    parser.add_argument('--compact', 
        action='store_true',
        help="use compact separators (',', ':')")
    parser.add_argument('--encoding', 
        default=None,
        metavar='ENC',
        help="Specify encoding of the input file")
    parser.add_argument('--record-buffered',
        dest='record_buffered',
        action='store_true',
        help="Economical buffering of writes at record, not collection (default), level")
    parser.add_argument('--ignore-errors',
        dest='ignore_errors',
        action='store_true',
        help="log errors but do not stop serialization")
    parser.add_argument('--use-ld-context',
        dest='use_ld_context',
        action='store_true',
        help="add a JSON-LD context to JSON output")
    parser.add_argument('--add-ld-context-item',
        dest='ld_context_items',
        action='append',
        metavar='TERM=URI',
        help="map a term to a URI and add it to the output's JSON LD context")

    args = parser.parse_args()

    # Keyword args to be used in all following json.dump* calls.
    dump_kw = {'sort_keys': True}
    if args.indent:
        dump_kw['indent'] = args.indent
    if args.compact:
        dump_kw['separators'] = (',', ':')

    item_sep = args.compact and ',' or ', '
    ignore_errors = args.ignore_errors

    sys.exit(main(args, dump_kw, item_sep, ignore_errors))

