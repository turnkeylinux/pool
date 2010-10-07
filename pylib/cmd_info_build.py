#!/usr/bin/python
"""Prints source build log for package
"""
import sys
import pool
import help

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s source-package[=version]" % sys.argv[0]

def main():
    args = sys.argv[1:]
    if not args:
        usage()
        
    source_package = args[0]
    try:
        path = pool.Pool().getpath_build_log(source_package)
    except pool.Error, e:
        fatal(e)

    for line in file(path).readlines():
        print line,

if __name__ == "__main__":
    main()
