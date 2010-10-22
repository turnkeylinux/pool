#!/usr/bin/python
"""Prints pool info

Options:
  --registered		Prints list of registered stocks and subpools (default)
  --stocks		Prints list of registered stocks
  --subpools		Prints list of registered subpools

  --build-root		Prints build-root
  --build-logs		Prints a list of build logs for source packages
  
  --pkgcache		Prints list of cached packages
  --source-versions	Prints versions of package sources in registered stocks

  -r --recursive	Lookup pool info recursively in subpools
"""
from os.path import *
import sys
import help
import getopt

from pool import Pool

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [-options]" % sys.argv[0]

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
        print "# stocks"
    print_stocks(pool)

    if pool.subpools:
        if pool.stocks:
            print
        print "# subpools"
        print_subpools(pool)
    
def print_stocks(pool):
    for stock in pool.stocks:
        addr = stock.link
        if stock.branch:
            addr += "#" + stock.branch
        print addr

def print_subpools(pool):
    for subpool in pool.subpools:
        print subpool.path

def print_build_root(pool):
    print pool.buildroot

def print_pkgcache(pool):
    pool.sync()
    for name, version in pool.pkgcache.list():
        print name + "=" + version

def print_source_versions(pool):
    pool.sync()

    output = []
    for stock, path, versions in pool.stocks.get_source_versions():
        for version in versions:
            package = basename(path) + "=" + version
            relative_path = dirname(path)
            output.append((package, stock.name, relative_path))

    if output:
        package_width = max([ len(vals[0]) for vals in output ])
        stock_name_width = max([ len(vals[1]) for vals in output ])

        for package, stock_name, relative_path in output:
            print "%s  %s  %s" % (package.ljust(package_width),
                                  stock_name.ljust(stock_name_width),
                                  relative_path)
def print_build_logs(pool):
    for log_name, log_version in pool.build_logs:
        print log_name + "=" + log_version

def info(func, recursive, pool=None):
    if pool is None:
        pool = Pool()

    if recursive:
        print "### POOL_DIR=" + pool.path

    func(pool)
    if recursive:
        for subpool in pool.subpools:
            print
            info(func, recursive, subpool)

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'hr',
                                   ['registered',
                                    'stocks',
                                    'subpools',
                                    'build-root',
                                    'build-logs',
                                    'pkgcache',
                                    'source-versions',
                                    'recursive'])
    except getopt.GetoptError, e:
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

            if opt == '--source-versions':
                rigid.set(print_source_versions)
    except RigidVal.AlreadySetError:
        fatal("conflicting options")
        
    func = rigid.get()
    if func is None:
        func = print_registered

    try:
        info(func, recursive)
    except Pool.Error, e:
        fatal(e)

if __name__ == "__main__":
    main()
