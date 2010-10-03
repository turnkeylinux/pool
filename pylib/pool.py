import os
from os.path import *

import shutil
import tempfile
import commands

from paths import Paths

import utils
import debsrc

from git import Git

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

def parse_package_id(package):
    """Parse package_id string

    <package> := package-name[=package-version]

    Returns (name, version)
    Returns (name, None) if no version is provided
    """
    if "=" in package:
        name, version = package.split("=", 1)
    else:
        name = package
        version = None

    return name, version

def fmt_package_id(name, version):
    if version:
        return "%s=%s" % (name, version)
    return name

def mkargs(*args):
    return tuple(map(commands.mkarg, args))

class PackageCache:
    """Class representing the pool's package cache"""
    def __init__(self, path):
        self.path = path

    def getpath(self, package):
        """Returns path to package if it exists, or None otherwise.

        <package> := package-name[=package-version]
        """

        name, version = parse_package_id(package)
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
            self.branch = None
            if "#" in self.name:
                self.branch = self.name.split("#")[1]

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
            
    @staticmethod
    def _parse_stock(stock):
        try:
            dir, branch = stock.split("#", 1)
        except ValueError:
            dir = stock
            branch = None

        return realpath(dir), branch

    def register(self, stock):
        dir, branch = self._parse_stock(stock)
        if not isdir(dir):
            raise Error("not a directory `%s'" % dir)

        try:
            git = Git(dir)
        except Git.Error:
            git = None

        if (not git and branch) or (git and branch and not git.show_ref(branch)):
            raise Error("no such branch `%s' at `%s'" % (branch, dir))

        if git and not branch:
            branch = basename(git.symbolic_ref("HEAD"))
        
        stock_name = basename(abspath(dir))
        if branch:
            stock_name += "#" + branch
        
        if self.stocks.has_key(stock_name):
            raise Error("stock already registered under name `%s'" % stock_name)

        self.stocks[stock_name] = self.Stock.init_create(join(self.path, stock_name), dir)
        
    def unregister(self, stock):
        dir, branch = self._parse_stock(stock)
        stock_name = basename(dir)
        if branch:
            stock_name += "#" + branch
            
        matches = [ stock for stock in self.stocks.values()
                    if stock.link == dir and (not branch or stock.branch == branch) ]
        if not matches:
            raise Error("no matches for unregister")

        if len(matches) > 1:
            raise Error("multiple implicit matches for unregister")

        stock = matches[0]
        shutil.rmtree(stock.path)
        del self.stocks[stock.name]

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

    def get_sources(self):
        """Recursively scan stocks for Debian source packages
        Returns an array of (/path/to/package-source/package-bin, version) tuples"""

        sources = []
        for stock in self.stocks.values():
            if stock.name in self.subpools.keys():
                continue

            stock_sources = debsrc.get_paths(stock.link)
            for stock_source in stock_sources:
                try:
                    version = debsrc.get_version(stock_source)
                    packages = debsrc.get_packages(stock_source)
                except debsrc.Error:
                    continue

                for package in packages:
                    sources.append((join(stock_source, package), version))

        return sources
    
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
        self.buildroot = os.readlink(self.paths.build.root)
        self.stocks = Stocks(self.paths.stocks, recursed_paths + [ dirname(self.paths.path) ])
        self.pkgcache = PackageCache(self.paths.pkgcache)
        self.tmpdir = os.environ.get("POOL_TMPDIR") or "/var/tmp/pool"
        mkdir(self.tmpdir)
    
    def register(self, stock):
        self.stocks.register(stock)
        
    def unregister(self, stock):
        self.stocks.unregister(stock)

    def print_info(self):
        for stock in self.stocks:
            addr = stock.link
            if stock.branch:
                addr += "#" + stock.branch
                
            print addr
            
    def _sync(self):
        """synchronise pool with registered stocks"""
        for binary in self.stocks.get_binaries():
            if self.pkgcache.exists(basename(binary)):
                continue

            self.pkgcache.add(binary)

    def _get_source_path(self, package):
        name, version = parse_package_id(package)
        for source_path, source_version in self.stocks.get_sources():
            if basename(source_path) == name:
                source_path = dirname(source_path)
                
                if version is None:
                    return source_path

                if source_version == version:
                    return source_path

        return None

    @sync
    def exists(self, package):
        """Check if package exists in pool -> Returns bool"""
        if self.pkgcache.exists(package):
            return True

        if self._get_source_path(package):
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
            
        packages |= set(self.pkgcache.list())
        packages |= set([ (basename(path), version)
                          for path, version in self.stocks.get_sources() ])
        
        if all_versions:
            return list(packages)

        newest = {}
        for name, version in packages:
            if not newest.has_key(name) or \
               debsrc.cmp_versions(newest[name], version) < 0:
                newest[name] = version

        return newest.items()

    @sync
    def getpath(self, package):
        """Get path to package in pool if it exists or None if it doesn't"""
        if '=' not in package:
            raise Error("getpath requires explicit version for `%s'" % package)
        
        path = self.pkgcache.getpath(package)
        if path:
            return path

        for subpool in self.stocks.get_subpools():
            path = subpool.getpath(package)
            if path:
                return path

        source_path = self._get_source_path(package)
        if not source_path:
            return None

        # get the precise package requested back from the cache
        package_name, package_version = parse_package_id(package)
        if not package_version:
            package_version = debsrc.get_version(source_path)
        package = fmt_package_id(package_name, package_version)

        build_outputdir = tempfile.mkdtemp(dir=self.tmpdir, prefix="%s-%s." % (package_name, package_version))

        print "### BUILDING PACKAGE: " + package
        print "###           SOURCE: " + source_path
        
        # build the package
        error = os.system("cd %s && deckdebuild %s %s" % mkargs(source_path, self.buildroot, build_outputdir))

        if error:
            shutil.rmtree(build_outputdir)
            raise Error("package `%s' failed to build" % package)

        print

        # copy *.debs and build output from output dir
        for fname in os.listdir(build_outputdir):
            fpath = join(build_outputdir, fname)
            if fname.endswith(".deb"):
                self.pkgcache.add(fpath)
            elif fname.endswith(".build"):
                shutil.copyfile(fpath, join(self.paths.build.logs, fname))

        shutil.rmtree(build_outputdir)

        path = self.pkgcache.getpath(package)
        if not path:
            raise Error("recently built package `%s' missing from cache" % package)
    
        return path
