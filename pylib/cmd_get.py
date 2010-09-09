#!/usr/bin/python
"""Get packages from pool

  If a package is specified without a version, get the newest package.
  If no packages are specified as arguments, get all the newest packages.

Options:
  -i --input <file>	file from which we read package list (- for stdin)
    
  -s --strict		fatal error on missing packages
  -q --quiet		suppress warnings about missing packages

  -t --tree		output dir is in a package tree format (like a repository)

"""
import sys
import help
import getopt

from os.path import *
import re

import pool
import utils

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options] <output-dir> [ package[=version] ... ]" % sys.argv[0]


exitcode = 0
def warn(s):
    global exitcode
    exitcode = 1
    
    print >> sys.stderr, "warning: " + str(s)
    
def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def read_packages(fh):
    packages = []
    for line in fh.readlines():
        line = re.sub(r'#.*', '', line)
        line = line.strip()
        if not line:
            continue
        packages.append(line)
    return packages
    
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:sqt',
                                   ['input=', 'strict', 'quiet', 'tree'])
    except getopt.GetoptError, e:
        usage(e)

    if not args:
        usage()

    outputdir = args[0]
    packages = args[1:]

    input = None
    opt_strict = False
    opt_quiet = False
    opt_tree = False
    
    for opt, val in opts:
        if opt in ('-i', '--input'):
            if val == '-':
                input = sys.stdin
            else:
                input = file(val, "r")
        elif opt in ('-s', '--strict'):
            opt_strict = True
        elif opt in ('-q', '--quiet'):
            opt_quiet = True
        elif opt in ('-t', '--tree'):
            opt_tree = True


    p = pool.Pool()
    if input:
        packages += read_packages(input)
    else:
        # if no packages specified, get all the newest versions
        if not packages:
            packages = [ "%s=%s" % (name, version)
                         for name, version in p.list() ]

    for package in packages:
        if not p.exists(package):
            if opt_strict:
                fatal("%s: no such package" % package)
            if not opt_quiet:
                warn("%s: no such package" % package)
            continue

        src_path = p.getpath(package)
        dst_path = join(outputdir, basename(src_path))

        if not exists(dst_path):
            utils.hardlink_or_copy(src_path, dst_path)

    sys.exit(exitcode)
        
if __name__=="__main__":
    main()
