import os
from os.path import *

import errno
import shutil

from paths import Paths

class Error(Exception):
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
    os.makedirs(str(p))

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

    def exists(self, package):
        """Returns True if <package> exists in cache.

        <package> := filename | package-name[=package-version]
        """

        if exists(join(self.path, basename(package))):
            return True
        
        if "=" in package:
            name, version = package.split("=", 1)
        else:
            name = package
            version = None

        for filename in os.listdir(self.path):
            if not isfile(filename) or not filename.endswith(".deb"):
                continue

            cached_name, cached_version = parse_deb_filename(filename)
            if name == cached_name and (version is None or version == cached_version):
                return True

        return False

    def add(self, path):
        """Add binary to cache. Hardlink if possible, copy otherwise"""

        cached_path = join(self.path, basename(path))
        try:
            os.link(path, cached_path)
        except OSError, e:
            if e[0] != errno.EXDEV:
                raise
            shutil.copyfile(path, cached_path)

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
            self.path = path
            self.link = os.readlink(join(path, "link"))

        def get_binaries(self):
            """Recursively scan stock for binaries -> list of filename"""

            binaries = []
            for dirpath, dnames, fnames in os.walk(self.link):
                for fname in fnames:
                    if not islink(fname) and isfile(fname) and fname.endswith(".deb"):
                        binaries.append(join(dirpath, fname))

            return binaries

    def __init__(self, path):
        self.path = path
        
        stocks = {}
        for stock_name in os.listdir(path):
            path_stock = join(path, stock_name)
            if not isdir(path_stock):
                continue

            stocks[stock_name] = self.Stock(path_stock)

        self.stocks = stocks
    
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

    def __iter__(self):
        return iter(self.stocks.values())

    def __len__(self):
        return len(self.stocks)

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
    
    def __init__(self, path=None):
        self.paths = PoolPaths(path)
        if not exists(self.paths.path):
            raise Error("no pool found (POOL_DIR=%s)" % dirname(self.paths.path))

        self.stocks = Stocks(self.paths.stocks)
        self.pkgcache = PackageCache(self.paths.pkgcache)

    def register(self, dir):
        if not isdir(dir):
            raise Error("not a directory `%s'" % dir)

        self.stocks.register(dir)
        
    def unregister(self, dir):
        self.stocks.unregister(dir)

    def print_info(self):
        for stock in self.stocks:
            print stock.link
            
    def _sync(self):
        """synchronise pool with registered stocks"""
        for stock in self.stocks:
            for binary in stock.get_binaries():
                if self.pkgcache.exists(basename(binary)):
                    continue

                self.pkgcache.add(binary)
    
    @sync
    def exists(self, package):
        """Check if package exists in pool -> Returns bool"""
        return self.pkgcache.exists(package)

    @sync
    def list(self, globs=[], all_versions=False, name_only=False):
        """List packages in pool -> list of packages"""
        if not isinstance(globs, (list, tuple)):
            globs = [ globs ]
            
        if all_versions and name_only:
            raise Error("conflicting otions")

        retarr = []
        if all_versions:
            for name, version in self.pkgcache.list():
                retarr.append("%s=%s" % (name, version))
        elif name_only:
            names = set()
            for name, version in self.pkgcache.list():
                names.add(name)

            for name in names:
                retarr.append(name)
        else:
            newest = {}
            for name, version in self.pkgcache.list():
                if not newest.has_key(name) or newest[name] < version:
                    newest[name] = version

            for name, version in newest.items():
                retarr.append("%s=%s" % (name, version))

        return retarr
