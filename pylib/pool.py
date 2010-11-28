import os
from os.path import *

import re
import shutil
import tempfile
import commands

from paths import Paths

from common import *
import verseek
import debversion

from git import Git
from forked import forked_constructor

import debinfo

class Error(Exception):
    pass

class CircularDependency(Error):
    pass

def deb_get_packages(srcpath):
    controlfile = join(srcpath, "debian/control")
    return [ re.sub(r'^.*?:', '', line).strip()
             for line in file(controlfile).readlines()
             if re.match(r'^Package:', line, re.I) ]

def parse_package_filename(filename):
    """Parses package filename -> (name, version)"""

    if not get_suffix(filename) in ('deb', 'udeb'):
        raise Error("not a package `%s'" % filename)

    name, version = filename.split("_")[:2]

    return name, version

def get_suffix(filename):
    try:
        return filename.rsplit(".", 1)[1]
    except IndexError:
        return None

class PackageCache:
    """Class representing the pool's package cache"""

    def _list_binaries(self):
        """List binaries in package cache -> list of package filenames"""
        for filename in os.listdir(self.path):
            filepath = join(self.path, filename)

            if not isfile(filepath) or not get_suffix(filename) in ('deb', 'udeb'):
                continue

            yield filename
            
    def _register(self, filename):
        name, version = parse_package_filename(filename)
        self.filenames[(name, version)] = filename
        if name in self.namerefs:
            self.namerefs[name] += 1
        else:
            self.namerefs[name] = 1

    def _unregister(self, name, version):
        del self.filenames[(name, version)]
        self.namerefs[name] -= 1
        if not self.namerefs[name]:
            del self.namerefs[name]
    
    def __init__(self, path):
        self.path = path

        self.filenames = {}
        self.namerefs = {}
        
        for filename in self._list_binaries():
            self._register(filename)

    def getpath(self, name, version):
        """Returns path to package if it exists, or None otherwise.
        """
        filename = self.filenames.get((name, version))
        if filename:
            return join(self.path, filename)
        return None
        
    def exists(self, name, version=None):
        """Returns True if package exists in cache.

        <name> := filename | package-name
        """

        if version:
            if (name, version) in self.filenames:
                return True
            else:
                return False

        if name in self.namerefs:
            return True

        if exists(join(self.path, basename(name))):
            return True

        return False

    def add(self, path):
        """Add binary to cache. Hardlink if possible, copy otherwise."""
        suffix = get_suffix(path)
        if not suffix in ('deb', 'udeb'):
            raise Error("illegal package suffix (%s)" % suffix)
        
        control_fields = debinfo.get_control_fields(path)
        name = control_fields['Package']
        version = control_fields['Version']
        
        if self.exists(name, version):
            return

        arch = control_fields['Architecture']
        filename = "%s_%s_%s.%s" % (name, version, arch, suffix)
        path_cached = join(self.path, filename)
        hardlink_or_copy(path, path_cached)

        self._register(filename)

    def remove(self, name, version):
        """Remove a specific package/version from the cache"""
        path = self.getpath(name, version)
        if not path:
            return
        os.remove(path)
        self._unregister(name, version)

    def list(self):
        """List packages in package cache -> list of (package, version)"""
        return self.filenames.keys()

def make_relative(root, path):
    """Return <path> relative to <root>.

    For example:
        make_relative("../../", "file") == "path/to/file"
        make_relative("/root", "/tmp") == "../tmp"
        make_relative("/root", "/root/backups/file") == "backups/file"
        
    """

    up_count = 0

    root = realpath(root).rstrip('/')
    path = realpath(path).rstrip('/')

    while True:
        if path == root or path.startswith(root.rstrip("/") + "/"):
            return ("../" * up_count) + path[len(root) + 1:]

        root = dirname(root).rstrip('/')
        up_count += 1

class StockBase(object):
    class Paths(Paths):
        files = [ 'link' ]

    @classmethod
    def create(cls, path, link):
        mkdir(path)
        paths = cls.Paths(path)
        os.symlink(realpath(link), paths.link)

    def __init__(self, path):
        self.paths = self.Paths(path)
        
        self.name = basename(path)
        self.link = os.readlink(self.paths.link)
        if not isdir(self.link):
            raise Error("stock link to non-directory `%s'" % self.link)

class StockPool(StockBase):
    """Class for managing a subpool-type stock"""
    def __init__(self, path, recursed_paths=[]):
        StockBase.__init__(self, path)
        if self.link in recursed_paths:
            raise CircularDependency("circular dependency detected `%s' is in recursed paths %s" %
                                     (self.link, recursed_paths))

        self.pool = Pool(self.link, recursed_paths)
        
class Stock(StockBase):
    """Class for managing a non-subpool-type stock."""

    class Paths(StockBase.Paths):
        files = [ 'index-sources', 'index-binaries', 'SYNC_HEAD', 'checkout' ]
                
    class SyncHead(object):
        """Magical attribute.

        Set writes to the stock's HEAD.
        Get reads the value from it.
        """
        def __get__(self, obj, type):
            path = obj.paths.SYNC_HEAD
            if exists(path):
                return file(path).read().rstrip()

            return None

        def __set__(self, obj, val):
            path = obj.paths.SYNC_HEAD
            if val is None:
                if exists(path):
                    os.remove(path)
            else:
                file(path, "w").write(val + "\n")

    sync_head = SyncHead()

    def _get_workdir(self):
        """Return an initialized workdir path.

        If the stock links to a plain directory, the workdir is simply its path.
        
        If the stock links to a git repository, the workdir will point to a
        persistent lightweight checkout of the desired branch.
        """
        if not self.branch:
            return self.link

        orig = Git(self.link)
        checkout_path = self.paths.checkout
        
        if not exists(checkout_path):
            mkdir(checkout_path)
            checkout = Git.init_create(checkout_path)
            checkout.set_alternates(orig)
        else:
            checkout = Git(checkout_path)

        def dup_branch(branch):
            # checkout latest changes
            commit = orig.rev_parse(branch)
            if not commit:
                raise Error("no such branch `%s' at %s" % (branch, self.link))
            checkout.update_ref("refs/heads/" + branch, commit)

        dup_branch(self.branch)
        checkout.checkout("-q", "-f", self.branch)

        if exists(join(checkout_path, "arena.internals")):
            dup_branch(self.branch + "-thin")

            command = "cd %s && sumo-open" % commands.mkarg(checkout_path)
            error = os.system(command)
            if error:
                raise Error("failed command: " + command)
            return join(checkout_path, "arena")

        # update tags
        for tag in orig.list_tags():
            checkout.update_ref("refs/tags/" + tag, orig.rev_parse(tag))

        return checkout_path

    class Workdir(object):
        """Magical attribute for performing lazy evaluation of workdir.
        If workdir is False, we evaluate its value.
        """
        def __get__(self, obj, type):
            if not obj._workdir:
                obj._workdir = obj._get_workdir()

            return obj._workdir

        def __set__(self, obj, val):
            obj._workdir = val

    workdir = Workdir()

    def _init_read_versions(self):
        source_versions = {}
        for dpath, dnames, fnames in os.walk(self.paths.index_sources):
            relative_path = make_relative(self.paths.index_sources, dpath)
            for fname in fnames:
                fpath = join(dpath, fname)
                versions = [ line.strip() for line in file(fpath).readlines() if line.strip() ]
                source_versions[join(relative_path, fname)] = versions

        return source_versions

    def __init__(self, path, pkgcache):
        StockBase.__init__(self, path)

        self.branch = None
        if "#" in self.name:
            self.branch = self.name.split("#")[1]

        self.source_versions = self._init_read_versions()
        self.workdir = None
        self.pkgcache = pkgcache

    def _sync_update_source_versions(self, dir):
        """update versions for a particular source package at <dir>"""
        packages = deb_get_packages(dir)
        versions = verseek.list(dir)

        relative_path = make_relative(self.workdir, dir)
        source_versions_path = join(self.paths.index_sources, relative_path)
        mkdir(source_versions_path)
        
        for package in packages:
            fh = file(join(source_versions_path, package), "w")
            for version in versions:
                print >> fh, version
            fh.close()

            self.source_versions[join(relative_path, package)] = versions

    def _sync_update_binary_versions(self, path):
        relative_path = make_relative(self.workdir, path)
        binary_version_path = join(self.paths.index_binaries, relative_path)
        mkdir(dirname(binary_version_path))
        file(binary_version_path, "w").truncate() # create zero length file
    
    def _sync(self, dir=None):
        """recursive sync back-end.
        updates versions of source packages and adds binaries to cache"""

        if dir is None:
            dir = self.workdir
            
        if isfile(join(dir, "debian/control")):
            return self._sync_update_source_versions(dir)

        for fname in os.listdir(dir):
            fpath = join(dir, fname)
            if not islink(fpath) and isfile(fpath) and get_suffix(fname) in ('deb', 'udeb'):
                self.pkgcache.add(fpath)
                self._sync_update_binary_versions(fpath)

            if isdir(fpath):
                self._sync(fpath)

    def binaries(self):
        """List package binaries for this stock -> [ relative/path/foo.deb, ... ]"""
        relative_paths = []
        for dpath, dnames, fnames in os.walk(self.paths.index_binaries):
            for fname in fnames:
                fpath = join(dpath, fname)
                relative_paths.append(make_relative(self.paths.index_binaries, fpath))

        return relative_paths
    binaries = property(binaries)

    def sources(self):
        """List package sources for this stock -> [ (relative/path/foo, versions), ... ]"""
        return self.source_versions.items()
    sources = property(sources)
        
    def sync(self):
        """sync stock by updating source versions and importing binaries into the cache"""

        if self.branch:
            if Git(self.link).rev_parse(self.branch) == self.sync_head:
                return

        # delete old cached versions
        for path in (self.paths.index_sources, self.paths.index_binaries):
            if exists(path):
                shutil.rmtree(path)
                mkdir(path)

        self.source_versions = {}
        
        self._sync()

        if self.branch:
            self.sync_head = Git(self.paths.checkout).rev_parse("HEAD")

class Stocks:
    """Class for managing and quering Pool Stocks in aggregate.

    Iterating an instance of this class produces all non-subpool type stocks.
    """
    def _load_stock(self, path_stock):
        stock = None
        try:
            stock = StockPool(path_stock, self.recursed_paths)
            self.subpools[stock.name] = stock.pool
        except CircularDependency:
            raise
        except Error:
            pass

        if not stock:
            stock = Stock(path_stock, self.pkgcache)

        self.stocks[stock.name] = stock

    def _load_stocks(self):
        self.stocks = {}
        self.subpools = {}
        
        for stock_name in os.listdir(self.path):
            path_stock = join(self.path, stock_name)
            if not isdir(path_stock):
                continue

            self._load_stock(path_stock)
    
    def __init__(self, path, pkgcache, recursed_paths=[]):
        self.path = path
        self.pkgcache = pkgcache
        self.recursed_paths = recursed_paths

        self._load_stocks()

    def reload(self):
        self._load_stocks()
            
    def __iter__(self):
        # iterate across all stocks except subpools
        return iter((stock for stock in self.stocks.values()
                     if not isinstance(stock, StockPool)))

    def __len__(self):
        return len(self.stocks) - len(self.subpools)

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

        stock_path = join(self.path, stock_name)
        Stock.create(stock_path, dir)
        self._load_stock(stock_path)
        
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

        del self.stocks[stock.name]
        if isinstance(stock, StockPool):
            del self.subpools[stock.name]
        else:
            # close sumo arena if it exists
            checkout_path = stock.paths.checkout
            if exists(join(checkout_path, "arena.internals")):
                command = "cd %s && sumo-close" % commands.mkarg(checkout_path)
                error = os.system(command)
                if error:
                    raise Error("failed command: " + command)

            # remove cached binaries compiled from this stock
            blacklist = set()
            for path, versions in stock.sources:
                name = basename(path)
                blacklist |= set([ (name, version) for version in versions ])

            blacklist |= set([ parse_package_filename(basename(path))
                               for path in stock.binaries ])

            removelist = set(self.pkgcache.list()) & blacklist
            for name, version in removelist:
                self.pkgcache.remove(name, version)

        shutil.rmtree(stock.paths.path)

    def sync(self):
        """sync all non-subpool stocks"""
        for stock in self:
            stock.sync()

    def get_source_path(self, name, version):
        """Return path of source package"""
        for stock in self:
            for path, versions in stock.sources:
                if basename(path) == name and version in versions:
                    return join(stock.workdir, dirname(path))

        return None

    def exists_source_version(self, name, version=None):
        """Returns true if the package source exists in any of the stocks.
        If version is None (default), any version will match"""

        for stock in self:
            for path, versions in stock.sources:
                if basename(path) == name:
                    if version is None:
                        return True

                    if version in versions:
                        return True

        return False
    
    def get_subpools(self):
        return self.subpools.values()

class PoolPaths(Paths):
    files = [ "pkgcache", "stocks", "tmp", "build/root", "build/logs" ]
    def __init__(self, path=None):
        if path is None:
            path = os.getenv("POOL_DIR", os.getcwd())
        path = join(realpath(path), ".pool")
        Paths.__init__(self, path)

def sync(method):
    def wrapper(self, *args, **kws):
        if self.autosync:
            self.sync()
        return method(self, *args, **kws)
    return wrapper

class _Pool(object):
    """Class for creating and controlling a Pool.
    This class's public methods map roughly to the pool's cli interface"""

    Error = Error
    class Subpools(object):
        def __get__(self, obj, type):
            return obj.stocks.get_subpools()

    subpools = Subpools()

    @staticmethod
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

    @staticmethod
    def fmt_package_id(name, version):
        """Format package_id string -> string"""

        if not version:
            raise Error("can't format package_id with unspecified version")

        return name + "=" + version

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

    def __init__(self, path=None, recursed_paths=[], autosync=True):
        """Initialize pool instance.

        if <autosync> is False, the user is expected to control syncing manually.
        """
        self.paths = PoolPaths(path)
        self.path = dirname(self.paths.path)
        if not exists(self.paths.path):
            raise Error("no pool found (POOL_DIR=%s)" % self.path)
        self.buildroot = os.readlink(self.paths.build.root)
        self.pkgcache = PackageCache(self.paths.pkgcache)
        self.stocks = Stocks(self.paths.stocks, self.pkgcache,
                             recursed_paths + [ self.path ])
        mkdir(self.paths.tmp)
        self.autosync = autosync
    
    def register(self, stock):
        self.stocks.register(stock)

    def unregister(self, stock):
        self.stocks.unregister(stock)

    @sync
    def exists(self, package):
        """Check if package exists in pool -> Returns bool"""

        name, version = self.parse_package_id(package)
        if self.pkgcache.exists(name, version):
            return True

        if self.stocks.exists_source_version(name, version):
            return True
        
        for subpool in self.subpools:
            if subpool.exists(package):
                return True

        return False

    @sync
    def _list(self, all_versions):
        """List packages in pool -> list of (name, version) tuples."""
        packages = set()
        for subpool in self.subpools:
            packages |= set(subpool._list(all_versions))
            
        packages |= set(self.pkgcache.list())
        for stock in self.stocks:
            for path, versions in stock.sources:
                package = basename(path)
                packages |= set([ (package, version) for version in versions ])
        
        if all_versions:
            return list(packages)

        newest = {}
        for name, version in packages:
            if not newest.has_key(name) or \
               debversion.compare(newest[name], version) < 0:
                newest[name] = version

        return newest.items()

    def list(self, all_versions=False):
        """List packages in pool -> list of packages.

        If all_versions is True, returns all versions of packages,
        otherwise, returns only the newest versions.
        """
        return [ self.fmt_package_id(name, version)
                 for name, version in self._list(all_versions) ]

    def resolve(self, unresolved):
        """Resolve a list of unresolved packages.
        If unresolved is a single unresolved package,
        return a single resolved package.
        
        If unresolved is a tuple or list of unresolved packages,
        return a list of resolved packages"""

        args = unresolved
        if not isinstance(args, (tuple, list)):
            args = (args,)

        packages = dict(self._list(all_versions=False))
        resolved = []

        for arg in args:
            name, version = self.parse_package_id(arg)
            if not version:
                if name not in packages:
                    raise Error("can't resolve non-existent package `%s'" % name)
                version = packages[name]

            resolved.append(self.fmt_package_id(name, version))
        
        if not isinstance(unresolved, (tuple, list)):
            return resolved[0]

        return resolved

    def _build_package_source(self, source_path, name, version):
        build_outputdir = tempfile.mkdtemp(dir=self.paths.tmp, prefix="%s-%s." % (name, version))

        package = self.fmt_package_id(name, version)

        print "### BUILDING PACKAGE: " + package
        print "###           SOURCE: " + source_path
        
        def mkargs(*args):
            return tuple(map(commands.mkarg, args))

        # seek to version, build the package, seek back
        verseek.seek(source_path, version)
        error = os.system("cd %s && deckdebuild %s %s" % mkargs(source_path, self.buildroot, build_outputdir))
        verseek.seek(source_path)
        
        if error:
            shutil.rmtree(build_outputdir)
            raise Error("package `%s' failed to build" % package)

        print

        # copy *.debs and build output from output dir
        for fname in os.listdir(build_outputdir):
            fpath = join(build_outputdir, fname)
            if get_suffix(fname) in ('deb', 'udeb'):
                self.pkgcache.add(fpath)
            elif fname.endswith(".build"):
                shutil.copyfile(fpath, join(self.paths.build.logs, fname))

        shutil.rmtree(build_outputdir)


    @sync
    def getpath_deb(self, package, build=True):
        """Get path to package in pool if it exists or None if it doesn't.

        By default if package exists only in source, build and cache it first.
        If build is False, we only return the path to packages in the cache.
        """
        name, version = self.parse_package_id(package)
        if version is None:
            raise Error("getpath_deb requires explicit version for `%s'" % package)
        
        path = self.pkgcache.getpath(name, version)
        if path:
            return path

        for subpool in self.subpools:
            path = subpool.getpath_deb(package, build)
            if path:
                return path

        if not build:
            return None

        source_path = self.stocks.get_source_path(name, version)
        if not source_path:
            return None

        self._build_package_source(source_path, name, version)

        path = self.pkgcache.getpath(name, version)
        if not path:
            raise Error("recently built package `%s' missing from cache" % package)
    
        return path

    class BuildLogs(object):
        def __get__(self, obj, type):
            for fname in os.listdir(obj.paths.build.logs):
                fpath = join(obj.paths.build.logs, fname)
                if not isfile(fpath) or not fname.endswith(".build"):
                    continue

                log_name, log_version = fname[:-len(".build")].split("_", 1)
                yield log_name, log_version

    build_logs = BuildLogs()

    def getpath_build_log(self, source_package):
        """Returns build log of specific version requested.
        If no specific version is requested, returns build-log of latest version"""

        name, version = self.parse_package_id(source_package)
        log_versions = []

        def get_log_path(log_name, log_version):
            return join(self.paths.build.logs, "%s_%s.build" % (log_name, log_version))
            
        for log_name, log_version in self.build_logs:
            if name == log_name:
                if version:
                    if version == log_version:
                        return get_log_path(name, version)
                else:
                    log_versions.append(log_version)

        if log_versions:
            log_versions.sort(debversion.compare)
            last_version = log_versions[-1]

            return get_log_path(name, last_version)
            
        for subpool in self.subpools:
            path = subpool.getpath_build_log(source_package)
            if path:
                return path

        return None

    @sync
    def gc(self, recurse=True):
        """Garbage collect stale data from the pool's caches"""

        whitelist = set()
        for stock in self.stocks:
            for path, versions in stock.sources:
                name = basename(path)
                whitelist |= set([ (name, version) for version in versions ])

            whitelist |= set([ parse_package_filename(basename(path))
                               for path in stock.binaries ])

        removelist = set(self.pkgcache.list()) - whitelist
        for name, version in removelist:
            self.pkgcache.remove(name, version)

        for stock in self.stocks:
            stock.sync_head = None

        if recurse:
            for subpool in self.subpools:
                subpool.gc(recurse)
            
    def sync(self):
        """synchronise pool with registered stocks"""
        self.stocks.sync()

class Pool(_Pool):
    """wrapper class that drops privileges in a sub-process if required.

    If privileges are dropped a proxy instance is returned which
    transparently passes method access to the real instance running inside
    the privilege reduced sub process.

    Otherwise, a normal pool instance is returned.
    """
    def __new__(cls, *args, **kws):
        pool = _Pool(*args, **kws)

        owner_uid = os.stat(pool.paths.path).st_uid
        owner_gid = os.stat(pool.paths.path).st_gid

        uid = os.getuid()

        if uid == owner_uid or uid != 0:
            return pool

        def f():
            os.setgid(owner_gid)
            os.setuid(owner_uid)
            reload(debinfo)
            return pool

        return forked_constructor(f)()
    
