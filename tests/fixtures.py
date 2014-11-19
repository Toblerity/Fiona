import os.path


def read_file(name):
    return open(os.path.join(os.path.dirname(__file__), name)).read()

feature_collection = read_file('data/collection.txt')
feature_collection_pp = read_file('data/collection-pp.txt')
feature_seq = read_file('data/sequence.txt')
feature_seq_pp_rs = read_file('data/sequence-pp.txt')
