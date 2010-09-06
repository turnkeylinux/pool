#!/usr/bin/python
"""unregister a package stock from the pool"""
import sys
import help
import pool

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <dir>" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def main():
    args = sys.argv[1:]
    
    if not args:
        usage()

    if len(args) != 1:
        usage("bad number of arguments")

    dir = args[0]
    try:
        pool.Pool().unregister(dir)
    except pool.Error, e:
        fatal(e)
        
if __name__=="__main__":
    main()

