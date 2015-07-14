import os.path


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()

# GeoJSON feature collection on a single line
feature_collection = read_file('data/collection.txt')

# Same as above but with pretty-print styling applied
feature_collection_pp = read_file('data/collection-pp.txt')

# One feature per line
feature_seq = read_file('data/sequence.txt')

# Same as above but each feature has pretty-print styling
feature_seq_pp_rs = read_file('data/sequence-pp.txt')
