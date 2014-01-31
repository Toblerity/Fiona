
import code
import logging
import pprint
import sys

import fiona


logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger('fiona.inspector')


def main(srcfile):
    
    with fiona.drivers(), fiona.open(srcfile) as src:
            
        code.interact(
            'Fiona %s Interactive Inspector\n'
            'Type "src.name", "src.schema", "next(src)", or "help(src)" '
            'for more information.' %  fiona.__version__,
            local=locals())


if __name__ == '__main__':
    
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m fiona.inspector",
        description="Open a data file and drop into an interactive interpreter")
    parser.add_argument(
        'src', 
        metavar='FILE', 
        help="Input dataset file name")
    args = parser.parse_args()
    
    main(args.src)

