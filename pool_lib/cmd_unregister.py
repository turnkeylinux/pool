#!/usr/bin/python
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Pool
#
# Pool is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""Unregister a package stock from the pool"""
import sys
import help
import pool

@help.usage(__doc__)
def usage():
    print("Syntax: %s /path/to/stock[#branch]" % sys.argv[0], file=sys.stderr)

def fatal(s):
    print("error: " + str(s), file=sys.stderr)
    sys.exit(1)

def main():
    args = sys.argv[1:]
    
    if not args:
        usage()

    if len(args) != 1:
        usage("bad number of arguments")

    stock = args[0]
    try:
        pool.Pool().unregister(stock)
    except pool.Error as e:
        fatal(e)
        
if __name__=="__main__":
    main()

