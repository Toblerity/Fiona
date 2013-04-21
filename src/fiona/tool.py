# The Fiona data tool.

import argparse
import fiona
import json
import logging
import pprint
import sys

def open_output(arg):
    if arg == sys.stdout:
        return arg
    else:
        return open(arg, 'wb')

if __name__ == '__main__':

    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
    logger = logging.getLogger('fiona.tool')

    parser = argparse.ArgumentParser(
        prog="python -mfiona.tool",
        description="Serialize a file's records or data description to GeoJSON")
    
    parser.add_argument('infile', 
        help="input file name")
    parser.add_argument('outfile',
        nargs='?', 
        help="output file name, defaults to stdout if omitted", 
        default=sys.stdout)
    parser.add_argument('-d', '--description',
        action='store_true', 
        help="serialize file's data description (schema) only")
    parser.add_argument('--encoding', 
        default=None,
        metavar='ENC',
        help="Specify encoding of the input file")
    parser.add_argument('-n', '--indent', 
        type=int,
        default=None,
        metavar='N',
        help="indentation level in N number of chars")
    parser.add_argument('--compact', 
        action='store_true',
        help="use compact separators (',', ':')")
    parser.add_argument('--record-buffered',
        dest='record_buffered',
        action='store_true',
        help="buffer writes at record, not collection (default), level")
    parser.add_argument('--ignore-errors',
        dest='ignore_errors',
        action='store_true',
        help="log errors but do not stop serialization")

    args = parser.parse_args()

    # Keyword args to be used in all following json.dump* calls.
    dump_kw = {}
    if args.indent:
        dump_kw['indent'] = args.indent
    if args.compact:
        dump_kw['separators'] = (',', ':')

    item_sep = args.compact and ',' or ', '
    ignore_errors = args.ignore_errors

    with open_output(args.outfile) as sink:

        with fiona.open(args.infile) as source:

            if args.description:
                meta = source.meta.copy()
                meta.update(name=args.infile)
                json.dump(meta, sink, **dump_kw)
            
            elif args.record_buffered:
                # Buffer GeoJSON data at the feature level for smaller
                # memory footprint.

                indented = bool(args.indent)
                rec_indent = "\n" + " " * (2 * (args.indent or 0))

                collection = {'type': 'FeatureCollection', 'features': []}
                head, tail = json.dumps(collection, **dump_kw).split('[]')
                
                sink.write(head)
                sink.write("[")
                
                itr = iter(source)
                
                # Try the first record.
                try:
                    first = next(itr)
                    if indented:
                        sink.write(rec_indent)
                    sink.write(
                        json.dumps(first, **dump_kw
                            ).replace("\n", rec_indent))
                except StopIteration:
                    pass
                except Exception as exc:
                    if ignore_errors:
                        logger.error(
                            "failed to serialize record 0 (%s), continuing",
                            exc)
                    else:
                        # Close up the GeoJSON, leaving it more or less valid
                        # no matter what happens above.
                        logger.critical(
                            "failed to serialize record %d (%s), quiting",
                            i, exc)
                        sink.write("]")
                        sink.write(tail)
                        if indented:
                            sink.write("\n")
                        raise
                
                # Because trailing commas aren't valid in JSON arrays
                # we'll write the item separator before each of the remaining
                # records.
                for i, rec in enumerate(itr, 1):
                    try:
                        if indented:
                            sink.write(rec_indent)
                        sink.write(item_sep)
                        sink.write(
                            json.dumps(rec, **dump_kw
                                ).replace("\n", rec_indent))
                    except Exception as exc:
                        if ignore_errors:
                            logger.error(
                                "failed to serialize record %d (%s), "
                                "continuing",
                                i, exc)
                        else:
                            # Close up the GeoJSON, leaving it more or less valid
                            # no matter what happens above.
                            logger.critical(
                                "failed to serialize record %d (%s), "
                                "quiting",
                                i, exc)
                            sink.write("]")
                            sink.write(tail)
                            if indented:
                                sink.write("\n")
                            raise
                
                # Close up the GeoJSON after passing over all records.
                sink.write("]")
                sink.write(tail)
                if indented:
                    sink.write("\n")

            else:
                # Buffer GeoJSON data at the collection level. The default.
                collection = {'type': 'FeatureCollection'}
                collection['features'] = list(source)
                json.dump(collection, sink, **dump_kw)

