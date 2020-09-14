#!/usr/bin/python
# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Pool
#
# Pool is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

"""Prints pool info

Options:
  --registered		Prints list of registered stocks and subpools (default)
  --stocks		Prints list of registered stocks
  --subpools		Prints list of registered subpools

  --build-root		Prints build-root
  --build-logs		Prints a list of build logs for source packages
  
  --pkgcache		Prints list of cached packages
  --stock-sources	Prints list of package sources in registered stocks
  --stock-binaries	Prints list of package binaries in registered stocks

  -r --recursive	Lookup pool info recursively in subpools
"""
from os.path import *
import sys
import help
import getopt

from pool import PoolKernel

def fatal(s):
    print("error: " + str(s), file=sys.stderr)
    sys.exit(1)

@help.usage(__doc__)
def usage():
    print("Syntax: %s [-options]" % sys.argv[0], file=sys.stderr)

class RigidVal:
    class AlreadySetError(Exception):
        pass
    
    def __init__(self):
        self.val = None

    def set(self, val):
        if self.val is not None:
            raise self.AlreadySetError()
        self.val = val

    def get(self):
        return self.val

def print_registered(pool):
    if pool.stocks:
        print("# stocks")
    print_stocks(pool)

    if pool.subpools:
        if pool.stocks:
            print()
        print("# subpools")
        print_subpools(pool)
    
def print_stocks(pool):
    for stock in pool.stocks:
        addr = stock.link
        if stock.branch:
            addr += "#" + stock.branch
        print(addr)

def print_subpools(pool):
    for subpool in pool.subpools:
        print(subpool.path)

def print_build_root(pool):
    print(pool.buildroot)

def print_pkgcache(pool):
    pool.sync()
    for name, version in pool.pkgcache.list():
        print(name + "=" + version)

def print_stock_inventory(stock_inventory):
    package_width = max([ len(vals[0]) for vals in stock_inventory ])
    stock_name_width = max([ len(vals[1]) for vals in stock_inventory ])

    for package, stock_name, relative_path in stock_inventory:
        print("%s  %s  %s" % (package.ljust(package_width),
                              stock_name.ljust(stock_name_width),
                              relative_path))
    
def print_stock_sources(pool):
    pool.sync()

    stock_inventory = []
    for stock in pool.stocks:
        for path, versions in stock.sources:
            for version in versions:
                package = basename(path) + "=" + version
                relative_path = dirname(path)
                stock_inventory.append((package, stock.name, relative_path))

    if stock_inventory:
        print_stock_inventory(stock_inventory)

def print_stock_binaries(pool):
    pool.sync()

    stock_inventory = []
    for stock in pool.stocks:
        for path in stock.binaries:
            package = basename(path)
            relative_path = dirname(path)
            stock_inventory.append((package, stock.name, relative_path))
            
    if stock_inventory:
        print_stock_inventory(stock_inventory)
        
def print_build_logs(pool):
    for log_name, log_version in pool.build_logs:
        print(log_name + "=" + log_version)

def info(func, recursive, pool=None):
    if pool is None:
        pool = PoolKernel()
        pool.drop_privileges()

    if recursive:
        print("### POOL_DIR=" + pool.path)

    func(pool)
    if recursive:
        for subpool in pool.subpools:
            print()
            info(func, recursive, subpool)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'hr',
                                   ['registered',
                                    'stocks',
                                    'subpools',
                                    'build-root',
                                    'build-logs',
                                    'pkgcache',
                                    'stock-sources',
                                    'stock-binaries',
                                    'recursive'])
    except getopt.GetoptError as e:
        usage(e)

    recursive = False
    rigid = RigidVal()
    try:
        for opt, val in opts:
            if opt == '-h':
                usage()

            if opt in ('-r', '--recursive'):
                recursive = True

            if opt == '--registered':
                rigid.set(print_registered)

            if opt == '--stocks':
                rigid.set(print_stocks)

            if opt == '--subpools':
                rigid.set(print_subpools)

            if opt == '--build-root':
                rigid.set(print_build_root)

            if opt == '--build-logs':
                rigid.set(print_build_logs)
                
            if opt == '--pkgcache':
                rigid.set(print_pkgcache)

            if opt == '--stock-sources':
                rigid.set(print_stock_sources)

            if opt == '--stock-binaries':
                rigid.set(print_stock_binaries)
                
    except RigidVal.AlreadySetError:
        fatal("conflicting options")
        
    func = rigid.get()
    if func is None:
        func = print_registered

    try:
        info(func, recursive)
    except PoolKernel.Error as e:
        fatal(e)

if __name__ == "__main__":
    main()
