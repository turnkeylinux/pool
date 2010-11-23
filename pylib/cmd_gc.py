#!/usr/bin/python
"""Garbage collect stale data from the pool's caches

Stale data includes:
A) A binary in the package cache that does not belong in any of the
   registered stocks.

   This includes binary packages which have since been removed from a
   registered stock.

B) Cached binary and source package versions.

Options:
  -R --disable-recursion    Disable recursive garbage collection of subpools

"""
import sys
import help
import pool
import getopt

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [ -options ]" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def main():
    args = sys.argv[1:]
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'Rh', ['disable-recursion'])
    except getopt.GetoptError, e:
        usage(e)

    opt_recurse = True
    for opt, val in opts:
        if opt == '-h':
            usage()
        if opt in ('-R', '--disable-recursion'):
            opt_recurse = False

    try:
        pool.Pool().gc(opt_recurse)
    except pool.Error, e:
        fatal(e)
        
if __name__=="__main__":
    main()
