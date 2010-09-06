#!/usr/bin/python
"""Initialize a new pool"""
import sys
import help
import pool

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s /path/to/build-chroot" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def main():
    args = sys.argv[1:]
    
    if not args:
        usage()
        
    if len(args) != 1:
        usage("bad number of arguments")

    buildroot = args[0]

    try:
        pool.Pool()
        fatal("pool already initialized")
    except pool.Error:
        pass
    
    try:
        pool.Pool.init_create(buildroot)
    except pool.Error, e:
        fatal(e)
    
if __name__=="__main__":
    main()

