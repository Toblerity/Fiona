# The Fiona data tool.

import argparse
import fiona
import json
import pprint
import sys

def open_input(arg):
    if arg == sys.stdin:
        return arg
    else:
        return fiona.open(arg, 'r')

def open_output(arg):
    if arg == sys.stdout:
        return arg
    else:
        return open(arg, 'wb')

if __name__ == '__main__':
    
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
    parser.add_argument('-i', '--indent', 
        type=int,
        default=None,
        metavar='N',
        help="indentation level in N number of chars")
    parser.add_argument('-c', '--compact', 
        action='store_true',
        help="use compact separators (',', ':')")
    parser.add_argument('-r', '--record-buffered',
        dest='record_buffered',
        action='store_true',
        help="buffer writes at record, not collection (default), level")

    args = parser.parse_args()

    dump_kw = {}
    if args.indent:
        dump_kw['indent'] = args.indent
    if args.compact:
        dump_kw['separators'] = (',', ':')

    item_sep = args.compact and ',' or ', '

    with open_output(args.outfile) as sink:

        with open_input(args.infile) as source:

            if args.description:
                meta = source.meta.copy()
                meta.update(name=args.infile)
                sink.write(json.dumps(meta, **dump_kw))
            
            elif args.record_buffered:
                # Buffer writes at the feature level for smaller memory
                # footprint.
                collection = {'type': 'FeatureCollection', 'features': []}
                head, tail = json.dumps(collection, **dump_kw).split('[]')
                rec_indent = " " * (2 * (args.indent or 0))

                try:
                    sink.write(head)
                    sink.write("[")
                    
                    itr = iter(source)
                    
                    # Because trailing commas aren't valid in JSON arrays
                    # we'll write the first record differently from the
                    # rest.
                    first = next(itr)
                    if args.indent:
                        sink.write("\n")
                        sink.write(rec_indent)
                    sink.write(
                        json.dumps(first, **dump_kw
                            ).replace("\n", "\n" + rec_indent))
                    
                    # Write the item separator before each of the remaining
                    # records.
                    for rec in itr:
                        if args.indent:
                            sink.write("\n")
                            sink.write(rec_indent)
                        sink.write(item_sep)
                        sink.write(
                            json.dumps(rec, **dump_kw
                                ).replace("\n", "\n" + rec_indent))

                except Exception as exc:
                    raise
                
                finally:
                    sink.write("]")
                    sink.write(tail)
                    if args.indent:
                        sink.write("\n")

            else:
                # Buffer writes at the collection level. The default.
                collection = {'type': 'FeatureCollection'}
                collection['features'] = list(source)
                json.dump(collection, sink, **dump_kw)

