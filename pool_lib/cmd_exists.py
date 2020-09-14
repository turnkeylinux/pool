#!/usr/bin/python
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Pool
#
# Pool is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""Check if package exists in pool

Prints true/false if <package> exists in the pool.
If true exitcode = 0, else exitcode = 1
"""
import sys
import help
import pool

@help.usage(__doc__)
def usage():
    print("Syntax: %s <package>[=<version>]" % sys.argv[0], file=sys.stderr)

def fatal(s):
    print("error: " + str(s), file=sys.stderr)
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
    except pool.Error as e:
        fatal(e)

    if istrue:
        print("true")
    else:
        print("false")
        sys.exit(1)
        
if __name__=="__main__":
    main()
