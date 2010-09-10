import os
from os.path import *

import shutil

from paths import Paths

import utils

class Error(Exception):
    pass

class CircularDependency(Error):
    pass

class PoolPaths(Paths):
    def __init__(self, path=None):
        if path is None:
            path = os.getenv("POOL_DIR", os.getcwd())
            
        path = join(realpath(path), ".pool")
        Paths.__init__(self, path,
                       ['pkgcache',
                        'stocks',
                        'build'])

        self.build = Paths(self.build,
                           ['root',
                            'logs'])

def mkdir(p):
    utils.makedirs(str(p))

def parse_deb_filename(filename):
    """Parses package filename -> (name, version)"""

    if not filename.endswith(".deb"):
        raise Error("not a package `%s'" % filename)
    
    name, version = filename.split("_")[:2]

    return name, version
    
class PackageCache:
    """Class representing the pool's package cache"""
    def __init__(self, path):
        self.path = path

    def getpath(self, package):
        """Returns path to package if it exists, or None otherwise.

        <package> := package-name[=package-version]
        """

        if "=" in package:
            name, version = package.split("=", 1)
        else:
            name = package
            version = None

        for filename in os.listdir(self.path):
            filepath = join(self.path, filename)
            
            if not isfile(filepath) or not filename.endswith(".deb"):
                continue

            cached_name, cached_version = parse_deb_filename(filename)
            if name == cached_name and (version is None or version == cached_version):
                return filepath

        return None
        
    def exists(self, package):
        """Returns True if <package> exists in cache.

        <package> := filename | package-name[=package-version]
        """

        if exists(join(self.path, basename(package))):
            return True

        return self.getpath(package) != None

    def add(self, path):
        """Add binary to cache. Hardlink if possible, copy otherwise"""

        cached_path = join(self.path, basename(path))
        utils.hardlink_or_copy(path, cached_path)

    def list(self):
        """List packages in package cache -> list of (package, version)"""
        arr = []
        for filename in os.listdir(self.path):
            name, version = parse_deb_filename(filename)
            arr.append((name, version))
        return arr

class Stocks:
    class Stock:
        @classmethod
        def init_create(cls, path, link):
            mkdir(path)
            os.symlink(realpath(link), join(path, "link"))

            return cls(path)

        def __init__(self, path):
            self.name = basename(path)
            self.path = path
            self.link = os.readlink(join(path, "link"))

            if not isdir(self.link):
                raise Error("stock link to non-directory `%s'" % stock.link)
            
    def __init__(self, path, recursed_paths=[]):
        self.path = path

        self.stocks = {}
        self.subpools = {}
        for stock_name in os.listdir(path):
            path_stock = join(path, stock_name)
            if not isdir(path_stock):
                continue

            stock = self.Stock(path_stock)
            if stock.link in recursed_paths:
                raise CircularDependency("circular dependency detected `%s' is in recursed paths %s" %
                                         (stock.link, recursed_paths))
            
            try:
                self.subpools[stock_name] = Pool(stock.link, recursed_paths)
            except CircularDependency:
                raise
            except Error:
                pass
            self.stocks[stock_name] = stock
            
    def register(self, dir):
        stock_name = basename(abspath(dir))
        if self.stocks.has_key(stock_name):
            raise Error("stock already registered under name `%s'" % stock_name)

        self.stocks[stock_name] = self.Stock.init_create(join(self.path, stock_name), dir)
        
    def unregister(self, dir):
        stock_name = basename(abspath(dir))
        if not self.stocks.has_key(stock_name) or \
           self.stocks[stock_name].link != realpath(dir):
            raise Error("no matches for unregister")

        shutil.rmtree(self.stocks[stock_name].path)
        del self.stocks[stock_name]

    def get_binaries(self):
        """Recursively scan stocks for binaries -> list of filename"""

        binaries = []
        for stock in self.stocks.values():
            if stock.name in self.subpools.keys():
                continue
            
            for dirpath, dnames, fnames in os.walk(stock.link):
                for fname in fnames:
                    fpath = join(dirpath, fname)
                    if not islink(fpath) and isfile(fpath) and fname.endswith(".deb"):
                        binaries.append(fpath)

        return binaries

    def get_subpools(self):
        return self.subpools.values()

    def __iter__(self):
        return iter(self.stocks.values())

def sync(method):
    def wrapper(self, *args, **kws):
        self._sync()
        return method(self, *args, **kws)
    return wrapper

class Pool:
    @classmethod
    def init_create(cls, buildroot, path=None):
        paths = PoolPaths(path)

        if not isdir(buildroot):
            raise Error("buildroot `%s' is not a directory" % buildroot)
        
        mkdir(paths.stocks)
        mkdir(paths.pkgcache)
        mkdir(paths.build)
        mkdir(paths.build.logs)
        os.symlink(buildroot, paths.build.root)

        return cls(path)
    
    def __init__(self, path=None, recursed_paths=[]):
        self.paths = PoolPaths(path)
        if not exists(self.paths.path):
            raise Error("no pool found (POOL_DIR=%s)" % dirname(self.paths.path))

        recursed_paths.append(dirname(self.paths.path))
        self.stocks = Stocks(self.paths.stocks, recursed_paths)
        self.pkgcache = PackageCache(self.paths.pkgcache)

    def register(self, dir):
        if not isdir(dir):
            raise Error("not a directory `%s'" % dir)

        if realpath(dir) == dirname(self.paths.path):
            raise Error("a pool can not contain itself")
        
        self.stocks.register(dir)
        
    def unregister(self, dir):
        self.stocks.unregister(dir)

    def print_info(self):
        for stock in self.stocks:
            print stock.link
            
    def _sync(self):
        """synchronise pool with registered stocks"""
        for binary in self.stocks.get_binaries():
            if self.pkgcache.exists(basename(binary)):
                continue

            self.pkgcache.add(binary)
    
    @sync
    def exists(self, package):
        """Check if package exists in pool -> Returns bool"""
        if self.pkgcache.exists(package):
            return True

        for subpool in self.stocks.get_subpools():
            if subpool.exists(package):
                return True

        return False

    @sync
    def list(self, all_versions=False):
        """List packages in pool -> list of (name, version) tuples.

        If all_versions is True, returns all versions of packages,
        otherwise, returns only the newest versions.
        """
        packages = set()
        for subpool in self.stocks.get_subpools():
            packages |= set(subpool.list(all_versions))
            
        if all_versions:
            for name, version in self.pkgcache.list():
                packages.add((name, version))

        else:
            newest = {}
            for name, version in self.pkgcache.list():
                if not newest.has_key(name) or newest[name] < version:
                    newest[name] = version

            for name, version in newest.items():
                packages.add((name, version))

        return list(packages)

    @sync
    def getpath(self, package):
        """Get path to package in pool if it exists or None if it doesn't"""
        path = self.pkgcache.getpath(package)
        if path:
            return path

        for subpool in self.stocks.get_subpools():
            path = subpool.getpath(package)
            if path:
                return path

        return None
