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
        description="Serialize a file to GeoJSON or view its description")
    
    parser.add_argument('infile', 
        help="input file name")
    parser.add_argument('outfile',
        nargs='?', 
        help="output file name, defaults to stdout if omitted", 
        default=sys.stdout)
    parser.add_argument('-d', '--description',
        action='store_true', 
        help="View input file description information only")
    parser.add_argument('-j', '--json',
        action='store_true', 
        help="Output as GeoJSON")
    parser.add_argument('-i', '--indent', 
        type=int,
        default=None,
        help="Number of indentation spaces")

    args = parser.parse_args()
    
    with open_output(args.outfile) as sink:

        with open_input(args.infile) as source:

            if args.description:
                meta = source.meta.copy()
                meta.update(name=args.infile)
                if args.json:
                    sink.write(json.dumps(meta, indent=args.indent))
                else:
                    sink.write("\nDescription of source: %r" % source)
                    print("\nCoordinate reference system (source.crs):")
                    pprint.pprint(meta['crs'], stream=sink)
                    print("\nFormat driver (source.driver):")
                    pprint.pprint(meta['driver'], stream=sink)
                    print("\nData description (source.schema):")
                    pprint.pprint(meta['schema'], stream=sink)
            else:
                collection = {'type': 'FeatureCollection'}
                collection['features'] = list(source)
                sink.write(json.dumps(collection, indent=args.indent))

