# The Fiona data tool.

if __name__ == '__main__':
    
    import argparse
    import fiona
    import json
    import pprint
    import sys
    
    parser = argparse.ArgumentParser(
        description="Serialize a file to GeoJSON or view its description")
    parser.add_argument('-i', '--info', 
        action='store_true', 
        help='View pretty printed description information only')
    parser.add_argument('-j', '--json', 
        action='store_true', 
        help='Output description as indented JSON')
    parser.add_argument('filename', help="data file name")
    args = parser.parse_args()

    with fiona.open(args.filename, 'r') as col:
        if args.info:
            if args.json:
                meta = col.meta.copy()
                meta.update(name=args.filename)
                print(json.dumps(meta, indent=2))
            else:
                print("\nDescription of: %r" % col)
                print("\nCoordinate reference system (col.crs):")
                pprint.pprint(meta['crs'])
                print("\nFormat driver (col.driver):")
                pprint.pprint(meta['driver'])
                print("\nData description (col.schema):")
                pprint.pprint(meta['schema'])
        else:
            collection = {'type': 'FeatureCollection'}
            collection['features'] = list(col)
            print(json.dumps(collection, indent=2))

