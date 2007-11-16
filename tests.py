
if __name__ == '__main__':
    import doctest
    import getopt
    import glob
    import sys
    
    verbosity = 0
    pattern = None

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'vt:')
        for o, a in opts:
            if o == '-v':
                verbosity = verbosity + 1
            if o == '-t':
                pattern = a
    except:
        pass

    docfiles = [
        'docs/reading-data.txt'
        ]
        
    if pattern:
        tests = [f for f in docfiles if f.find(pattern) == 0]
    else:
        tests = docfiles
        
    for file in tests:
        doctest.testfile(file, verbosity)

