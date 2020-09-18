# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Pool
#
# Pool is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import os
from os.path import *

import re
import shutil
import tempfile
import subprocess

from debian import debfile

from .paths import Paths

import errno
import verseek_lib as verseek
from . import debversion

from gitwrapper import Git

from forked import forked_constructor
from fnmatch import fnmatch
import imp

class PoolError(Exception):
    pass

class CircularDependency(PoolError):
    pass

def deb_get_packages(srcpath):
    controlfile = join(srcpath, "debian/control")
    return [ re.sub(r'^.*?:', '', line).strip()
             for line in file(controlfile).readlines()
             if re.match(r'^Package:', line, re.I) ]

def parse_package_filename(filename):
    """Parses package filename -> (name, version)"""

    if not get_suffix(filename) in ('deb', 'udeb'):
        raise PoolError("not a package `%s'" % filename)

    name, version = filename.split("_")[:2]

    return name, version

def get_suffix(filename):
    try:
        return filename.rsplit(".", 1)[1]
    except IndexError:
        return None

def hardlink_or_copy(src, dst):
    if exists(dst):
        os.remove(dst)

    try:
        os.link(src, dst)
    except OSError as e:
        if e[0] != errno.EXDEV:
            raise
        shutil.copyfile(src, dst)

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
            raise PoolError("illegal package suffix (%s)" % suffix)

        deb = debfile.DebFile(path)
        name = deb.debcontrol()['Package']
        version = deb.debcontrol()['Version']

        if self.exists(name, version):
            return

        arch = deb.debcontrol()['Architecture']
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
        return list(self.filenames.keys())

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

def mkdir(path):
    path = str(path)
    try:
        os.makedirs(path)
    except OSError as e:
        if e[0] != errno.EEXIST:
            raise

class StockBase(object):
    class StockBaseError(Exception):
        pass

    class Paths(Paths):
        files = [ 'link' ]

    @classmethod
    def create(cls, path, link):
        mkdir(path)
        paths = cls.Paths(path)
        os.symlink(abspath(link), paths.link)

    def __init__(self, path):
        self.paths = self.Paths(path)

        self.name = basename(path)
        if not exists(self.paths.link):
            raise StockBaseError("stock link doesn't exist")

        self.link = os.readlink(self.paths.link)
        if not isdir(self.link):
            raise StockBaseError("stock link to non-directory `%s'" % self.link)

class StockPool(StockBase):
    """Class for managing a subpool-type stock"""
    def __init__(self, path, recursed_paths=[]):
        StockBase.__init__(self, path)
        if self.link in recursed_paths:
            raise CircularDependency("circular dependency detected `%s' is in recursed paths %s" %
                                     (self.link, recursed_paths))

        self.pool = PoolKernel(self.link, recursed_paths)

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
                raise self.Error("no such branch `%s' at %s" % (branch, self.link))
            checkout.update_ref("refs/heads/" + branch, commit)

        dup_branch(self.branch)
        checkout.checkout("-q", "-f", self.branch)

        if exists(join(checkout_path, "arena.internals")):
            dup_branch(self.branch + "-thin")

            command = "cd %s && sumo-open" % subprocess.mkarg(checkout_path)
            error = os.system(command)
            if error:
                raise self.StockError("failed command: " + command)
            return join(checkout_path, "arena")

        # update tags
        for tag in checkout.list_tags():
            checkout.remove_tag(tag)

        for tag in orig.list_tags():
            try:
                checkout.update_ref("refs/tags/" + tag, orig.rev_parse(tag))
            except:
                continue

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
                print(version, file=fh)
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
        return list(self.source_versions.items())
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
        except (PoolError, Stock.Error):
            pass

        if not stock:
            try:
                stock = Stock(path_stock, self.pkgcache)
            except StockError:
                return

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
        return iter((stock for stock in list(self.stocks.values())
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

        return abspath(dir), branch

    def register(self, stock):
        dir, branch = self._parse_stock(stock)
        if not isdir(dir):
            raise PoolError("not a directory `%s'" % dir)

        try:
            git = Git(dir)
        except Git.Error:
            git = None

        if (not git and branch) or (git and branch and not git.show_ref(branch)):
            raise PoolError("no such branch `%s' at `%s'" % (branch, dir))

        if git and not branch:
            branch = basename(git.symbolic_ref("HEAD"))

        stock_name = basename(abspath(dir))
        if branch:
            stock_name += "#" + branch

        if stock_name in self.stocks:
            raise PoolError("stock already registered under name `%s'" % stock_name)

        stock_path = join(self.path, stock_name)
        Stock.create(stock_path, dir)
        self._load_stock(stock_path)

    def unregister(self, stock):
        dir, branch = self._parse_stock(stock)
        stock_name = basename(dir)
        if branch:
            stock_name += "#" + branch

        matches = [ stock for stock in list(self.stocks.values())
                    if realpath(stock.link) == realpath(dir) and (not branch or stock.branch == branch) ]
        if not matches:
            raise PoolError("no matches for unregister")

        if len(matches) > 1:
            raise PoolError("multiple implicit matches for unregister")

        stock = matches[0]

        del self.stocks[stock.name]
        if isinstance(stock, StockPool):
            del self.subpools[stock.name]
        else:
            # close sumo arena if it exists
            checkout_path = stock.paths.checkout
            if exists(join(checkout_path, "arena.internals")):
                command = "cd %s && sumo-close" % subprocess.mkarg(checkout_path)
                error = os.system(command)
                if error:
                    raise PoolError("failed command: " + command)

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
        return list(self.subpools.values())

class PoolPaths(Paths):
    files = [ "pkgcache", "stocks", "tmp", "build/root", "build/logs", "build/buildinfo", "srcpkgcache" ]

    def __new__(cls, path, create=False):
        return str.__new__(cls, path)

    def __init__(self, path=None, create=False):

        def pool_realpath(p):
            return join(realpath(p), ".pool")

        def get_default_path(create):
            path_cwd = os.getcwd()
            path_env = os.environ.get("POOL_DIR") or path_cwd

            if create:
                if isdir(pool_realpath(path_env)):
                    return path_cwd
                else:
                    return path_env

            else:
                if isdir(pool_realpath(path_cwd)):
                    return path_cwd
                else:
                    return path_env

        if path is None:
            path = get_default_path(create)

        path = pool_realpath(path)
        Paths.__init__(self, path)

def sync(method):
    def wrapper(self, *args, **kws):
        if self.autosync:
            self.sync()
        return method(self, *args, **kws)
    return wrapper

class PoolKernel(object):
    """Class for creating and controlling a Pool.
    This class's public methods map roughly to the pool's cli interface"""

    PoolError = PoolError
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
            raise PoolError("can't format package_id with unspecified version")

        return name + "=" + version

    def __init__(self, path=None, recursed_paths=[], autosync=True):
        """Initialize pool instance.

        if <autosync> is False, the user is expected to control syncing manually.
        """
        self.paths = PoolPaths(path)
        self.path = dirname(self.paths.path)
        if not exists(self.paths.path):
            raise PoolError("no pool found (POOL_DIR=%s)" % self.path)

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
            if name not in newest or \
               debversion.compare(newest[name], version) < 0:
                newest[name] = version

        return list(newest.items())

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
                    raise PoolError("can't resolve non-existent package `%s'" % name)
                version = packages[name]

            resolved.append(self.fmt_package_id(name, version))

        if not isinstance(unresolved, (tuple, list)):
            return resolved[0]

        return resolved

    def _build_package_source(self, source_path, name, version, source=False):
        build_outputdir = tempfile.mkdtemp(dir=self.paths.tmp, prefix="%s-%s." % (name, version))

        package = self.fmt_package_id(name, version)

        print("### BUILDING PACKAGE: " + package)
        print("###           SOURCE: " + source_path)

        def mkargs(*args):
            return tuple(map(subprocess.mkarg, args))

        # seek to version, build the package, seek back
        verseek.seek(source_path, version)
        if source:
            error = os.system("cd %s && deckdebuild --build-source %s %s" % mkargs(
                    source_path, self.buildroot, build_outputdir))
        else:
            error = os.system("cd %s && deckdebuild %s %s" % mkargs(source_path, self.buildroot, build_outputdir))
        verseek.seek(source_path)

        if error:
            shutil.rmtree(build_outputdir)
            raise PoolError("package `%s' failed to build" % package)

        print()

        # copy *.debs and build output from output dir
        for fname in os.listdir(build_outputdir):
            fpath = join(build_outputdir, fname)
            fname_part, ext_part = splitext(fname)
            if get_suffix(fname) in ('deb', 'udeb'):
                self.pkgcache.add(fpath)
            elif fname.endswith(".build"):
                shutil.copyfile(fpath, join(self.paths.build.logs, fname))
            elif fname.endswith(".buildinfo"):
                shutil.copyfile(fpath, join(self.paths.build.buildinfo, fname))
            elif ext_part in ('.gz', '.xz', '.bz2') and splitext(fname_part)[1] == '.tar':
                shutil.copyfile(fpath, join(self.paths.srcpkgcache, fname))

        shutil.rmtree(build_outputdir)


    @sync
    def getpath_deb(self, package, build=True, source=False):
        """Get path to package in pool if it exists or None if it doesn't.

        By default if package exists only in source, build and cache it first.
        If build is False, we only return the path to packages in the cache.
        """
        name, version = self.parse_package_id(package)
        if version is None:
            raise PoolError("getpath_deb requires explicit version for `%s'" % package)

        path = self.pkgcache.getpath(name, version)
        if path:
            return path

        for subpool in self.subpools:
            path = subpool.getpath_deb(package, build, source)
            if path:
                return path

        if not build:
            return None

        source_path = self.stocks.get_source_path(name, version)
        if not source_path:
            return None

        self._build_package_source(source_path, name, version, source)

        path = self.pkgcache.getpath(name, version)
        if not path:
            raise PoolError("recently built package `%s' missing from cache" % package)

        return path

    class BuildLogs(object):
        def __get__(self, obj, type):
            arr = []
            for fname in os.listdir(obj.paths.build.logs):
                fpath = join(obj.paths.build.logs, fname)
                if not isfile(fpath) or not fname.endswith(".build"):
                    continue

                log_name, log_version = fname[:-len(".build")].split("_", 1)
                arr.append((log_name, log_version))
            return arr

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

    def drop_privileges(self, pretend=False):
        """Set the uid and gid of the current process to that of the pool.
        Returns whether or not we dropped privileges.

        if <pretend> is True, we don't actually drop privileges.
        """
        pool_uid = os.stat(self.paths.path).st_uid
        pool_gid = os.stat(self.paths.path).st_gid

        if os.getuid() != 0 or os.getuid() == pool_uid:
            return False

        if not pretend:
            os.setgid(pool_gid)
            os.setuid(pool_uid)
            imp.reload(debfile)

        return True

    def sync(self):
        """synchronise pool with registered stocks"""
        self.stocks.sync()

def get_treedir(pkgname):
    if pkgname.startswith("lib"):
        return join(pkgname[:4], pkgname)
    else:
        return join(pkgname[:1], pkgname)

class Pool(object):
    PoolError = PoolError

    class PackageList(list):
        def __init__(self, sequence=None):
            if sequence:
                list.__init__(self, sequence)
            else:
                list.__init__(self)

            self.missing = []

    parse_package_id = staticmethod(PoolKernel.parse_package_id)
    fmt_package_id = staticmethod(PoolKernel.fmt_package_id)

    @classmethod
    def init_create(cls, buildroot, path=None):
        paths = PoolPaths(path, create=True)
        if isdir(paths.path):
            raise PoolError("pool already initialized")

        if not isdir(buildroot):
            raise PoolError("buildroot `%s' is not a directory" % buildroot)

        mkdir(paths.stocks)
        Git.set_gitignore(paths.stocks, Stock.Paths.files)

        mkdir(paths.pkgcache)
        Git.anchor(paths.pkgcache)
        Git.set_gitignore(paths.pkgcache, ["*.deb", "*.udeb"])

        mkdir(paths.srcpkgcache)
        Git.anchor(paths.srcpkgcache)
        Git.set_gitignore(paths.srcpkgcache, ['*.tar.xz', '*.tar.gz', '*.tar.bz2'])

        mkdir(paths.build)

        mkdir(paths.build.logs)
        Git.anchor(paths.build.logs)
        Git.set_gitignore(paths.build.logs, ["*.build"])

        mkdir(paths.build.buildinfo)
        Git.anchor(paths.build.buildinfo)
        Git.set_gitignore(paths.build.buildinfo, ['*.buildinfo'])

        Git.set_gitignore(paths.path, ["tmp"])

        os.symlink(buildroot, paths.build.root)

        return cls(path)

    def __init__(self, path=None):
        kernel = PoolKernel(path)
        if kernel.drop_privileges(pretend=True):
            def f():
                kernel.drop_privileges()
                return kernel
            kernel = forked_constructor(f, print_traceback=True)()
        self.kernel = kernel

    def __getattr__(self, name):
        return getattr(self.kernel, name)

    def list(self, all_versions=False, *globs):
        """List packages in pool (sorted) -> Pool.PackageList (list + .missing attr)

        If no globs are specified, lists all packages.
        Globs that didn't match are listed in PackageList.missing
        """
        assert isinstance(all_versions, bool)

        def filter_packages(packages, globs):
            filtered = Pool.PackageList()
            for glob in globs:
                matches = []
                for package in packages:
                    name, version = Pool.parse_package_id(package)
                    if fnmatch(name, glob):
                        matches.append(package)

                if not matches:
                    filtered.missing.append(glob)
                else:
                    filtered += matches

            return filtered

        packages = Pool.PackageList(self.kernel.list(all_versions))
        if globs:
            packages = filter_packages(packages, globs)

        def _cmp(a, b):
            a = Pool.parse_package_id(a)
            b = Pool.parse_package_id(b)
            val = cmp(b[0], a[0])
            if val != 0:
                return val
            return debversion.compare(a[1], b[1])

        packages.sort(cmp=_cmp, reverse=True)
        return packages

    def get(self, output_dir, packages, tree_fmt=False, strict=False, source=False):
        """get packages to output_dir -> resolved Pool.PackageList of packages we got

        If strict missing packages raise an exception,
        otherwise they are listed in .missing attr of the returned PackageList
        """

        self.kernel.autosync = False
        self.kernel.sync()

        resolved = Pool.PackageList()
        unresolved = []
        for package in packages:
            if not self.kernel.exists(package):
                if strict:
                    raise PoolError("no such package (%s)" % package)
                resolved.missing.append(package)
                continue

            if '=' in package:
                resolved.append(package)
            else:
                unresolved.append(package)

        if unresolved:
            resolved += self.kernel.resolve(unresolved)

        try:
            for package in resolved:
                path_from = self.kernel.getpath_deb(package, source=source)
                fname = basename(path_from)

                if tree_fmt:
                    package_name = package.split("=")[0]
                    path_to = join(output_dir, get_treedir(package_name), fname)
                    mkdir(dirname(path_to))
                else:
                    path_to = join(output_dir, basename(path_from))

                if not exists(path_to):
                    hardlink_or_copy(path_from, path_to)
        finally:
            self.kernel.autosync = True

        return resolved

