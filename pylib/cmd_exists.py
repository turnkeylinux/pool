#!/usr/bin/python
"""Check if package exists in pool

Prints true/false if <package> exists in the pool.
If true exitcode = 0, else exitcode = 1
"""
import sys
import help
import pool

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s <package>[=<version>]" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def main():
    args = sys.argv[1:]
    
    if not args:
        usage()
        
    if len(args) != 1:
        usage("bad number of arguments")

    package = args[0]
    try:
        istrue = pool.Pool().exists(package)
    except pool.Error, e:
        fatal(e)

    if istrue:
        print "true"
    else:
        print "false"
        sys.exit(1)
        
if __name__=="__main__":
    main()
