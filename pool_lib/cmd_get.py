#!/usr/bin/python
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Pool
#
# Pool is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""Get packages from pool

  If a package is specified without a version, get the newest package.
  If no packages are specified as arguments, get all the newest packages.

Options:
  -i --input <file>	file from which we read package list (- for stdin)
    
  -s --strict		fatal error on missing packages
  -q --quiet		suppress warnings about missing packages

  -t --tree		output dir is in a package tree format (like a repository)

  -o --source       build source packages in addition to binary packages

"""
import sys
import help
import getopt

from os.path import *
import re

from pool import Pool

@help.usage(__doc__)
def usage():
    print("Syntax: %s [-options] <output-dir> [ package[=version] ... ]" % sys.argv[0], file=sys.stderr)


exitcode = 0
def warn(s):
    global exitcode
    exitcode = 1
    
    print("warning: " + str(s), file=sys.stderr)
    
def fatal(s):
    print("error: " + str(s), file=sys.stderr)
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
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'i:sqto',
                                       ['input=', 'strict', 'quiet', 'tree', 'source'])
    except getopt.GetoptError as e:
        usage(e)

    if not args:
        usage()

    outputdir = args[0]
    packages = args[1:]

    input = None
    opt_strict = False
    opt_quiet = False
    opt_tree = False
    opt_source = False
    
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
        elif opt in ('-o', '--source'):
            opt_source = True

    pool = Pool()
    
    if input:
        packages += read_packages(input)

    if not args[1:] and not input:
        # if no packages specified, get all the newest versions
        packages = pool.list()

    try:
        packages = pool.get(outputdir, packages, tree_fmt=opt_tree, strict=opt_strict, source=opt_source)
    except pool.Error as e:
        fatal(e)

    if not opt_quiet:
        for package in packages.missing:
            warn("no such package (%s)" % package)
            
    sys.exit(exitcode)
        
if __name__=="__main__":
    main()
