# Copyright (c) TurnKey GNU/Linux - http://www.turnkeylinux.org
#
# This file is part of Pool
#
# Pool is free software; you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation; either version 3 of the License, or (at your
# option) any later version.

import os
from os.path import (
        exists, isfile, isdir, islink, dirname, basename, abspath,
        join, splitext, abspath, realpath, relpath)
import re
import shlex
import sys
import shutil
import tempfile
import subprocess
import importlib
from contextlib import contextmanager
from typing import (
    Optional, Union, Generator, Type, Iterator,
    TypeVar, Iterable, no_type_check, cast,
    List # in a couple of places, if "list" isn't used, there are type errors?
)
import logging

from debian import debfile, debian_support
# TODO this should be removed - also see related commented code below
#from functools import cmp_to_key

import errno
import verseek_lib as verseek

from gitwrapper import Git, GitError

from .forked import forked_constructor
from fnmatch import fnmatch

logger = logging.getLogger('pool')
# allow 'DEBUG' env var to override 'POOL_LOG_LEVEL'
if 'DEBUG' in os.environ.keys():
    level = 'debug'
else:
    level = os.getenv('POOL_LOG_LEVEL', '').lower()

if level == 'info':
    loglevel = logging.INFO
elif level == 'debug':
    loglevel = logging.DEBUG
elif level in ('', 'warn', 'warning'):
    loglevel = logging.WARNING
elif level in ('err', 'error', 'fatal'):
    loglevel = logging.ERROR
else:
    loglevel = logging.WARNING
logging.basicConfig(
    format='%(asctime)s - [%(levelname)-7s] ' +
           '%(filename)s:%(lineno)d %(message)s',
    level=loglevel)

AnyPath = Union[str, os.PathLike]


def str_path(p: AnyPath) -> str:
    p = os.fspath(p)
    assert isinstance(p, str)
    return p


class PoolError(Exception):
    pass


class StockError(PoolError):
    pass


class CircularDependency(PoolError):
    pass


def deb_get_packages(srcpath: AnyPath) -> list[str]:
    path = str_path(srcpath)
    controlfile = join(path, "debian/control")

    lines = []
    for line in open(controlfile):
        if re.match(r'^Package:', line, re.I):
            lines.append(re.sub(r'^.*?:', '', line).strip())
    return lines


def parse_package_filename(filename: str) -> tuple[str, str]:
    """Parses package filename -> (name, version)"""

    if not splitext(filename)[1] in (".deb", ".udeb"):
        raise PoolError(f"not a package `{filename}'")

    name, version = filename.split("_")[:2]

    return name, version


def hardlink_or_copy(src: AnyPath, dst: AnyPath) -> None:
    src = os.fspath(src)
    dst = os.fspath(dst)
    if exists(dst):
        os.remove(dst)

    try:
        os.link(src, dst)
    except OSError as e:
        if e.args[0] != errno.EXDEV:
            raise
        shutil.copyfile(src, dst)


@contextmanager
def in_dir(path: AnyPath) -> Generator[None, None, None]:
    '''context manager to perform an operation within a specified directory'''
    cwd = os.getcwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(cwd)


class PackageCache:
    """Class representing the pool's package cache"""

    def _list_binaries(self) -> Generator[str, None, None]:
        """List binaries in package cache -> list of package filenames"""
        for filename in os.listdir(self.path):
            filepath = join(self.path, filename)

            if (
                    not isfile(filepath) or
                    not splitext(filename)[1] in (".deb", ".udeb")
               ):
                continue

            yield filename

    def _register(self, filename: str) -> None:
        logger.debug(f'PackageCache({self.path})._register({filename})')
        name, version = parse_package_filename(filename)
        self.filenames[(name, version)] = filename
        if name in self.namerefs:
            self.namerefs[name] += 1
        else:
            self.namerefs[name] = 1

    def _unregister(self, name: str, version: str) -> None:
        logger.debug(
                f'PackageCache({self.path})._unregister({name}, {version})')
        del self.filenames[(name, version)]
        self.namerefs[name] -= 1
        if not self.namerefs[name]:
            del self.namerefs[name]

    def __init__(self, path: AnyPath):
        self.path = str_path(path)

        self.filenames: dict[tuple[str, str], str] = {}
        self.namerefs: dict[str, int] = {}

        for filename in self._list_binaries():
            self._register(filename)

    def getpath(self, name: str, version: str) -> Optional[str]:
        """Returns path to package if it exists, or None otherwise.
        """
        filename = self.filenames.get((name, version))
        if filename:
            return join(self.path, filename)
        return None

    def exists(self, name: str, version: Optional[str] = None) -> bool:
        """Returns True if package exists in cache.

        <name> := filename | package-name
        """

        if version:
            return (name, version) in self.filenames

        if name in self.namerefs:
            return True

        return exists(join(self.path, basename(name)))

    def add(self, path: AnyPath) -> None:
        """Add binary to cache. Hardlink if possible, copy otherwise."""
        path_ = str_path(path)
        suffix = splitext(path_)[1]
        if suffix not in (".deb", ".udeb"):
            raise PoolError(f"illegal package suffix ({suffix})")

        deb = debfile.DebFile(path_)
        name = deb.debcontrol()["Package"]
        version = deb.debcontrol()["Version"]

        if self.exists(name, version):
            return

        arch = deb.debcontrol()["Architecture"]
        filename = f"{name}_{version}_{arch}{suffix}"
        path_cached = join(self.path, filename)
        hardlink_or_copy(path_, path_cached)

        self._register(filename)

    def remove(self, name: str, version: str) -> None:
        """Remove a specific package/version from the cache"""
        path = self.getpath(name, version)
        if not path:
            return
        os.remove(path)
        self._unregister(name, version)

    def list(self) -> list[tuple[str, str]]:
        """List packages in package cache -> list of (package, version)"""
        return list(self.filenames.keys())


def mkdir(path: AnyPath) -> None:
    path_ = str_path(path)
    try:
        os.makedirs(path_)
    except OSError as e:
        if e.args[0] != errno.EEXIST:
            raise


class StockBase:
    class StockBaseError(Exception):
        pass

    @classmethod
    def create(cls, path: str, link: str) -> None:
        logger.debug(f'{cls}(path={path!r}, link={link!r}')
        mkdir(path)
        logger.debug(f'mkdir {path}')
        os.symlink(abspath(link), join(path, 'link'))
        logger.debug(f'ln -s {link} {path}/link')

    @property
    def sources(self) -> list[tuple[str, list[str]]]:
        ...

    @property
    def binaries(self) -> list[str]:
        ...

    def sync(self) -> None:
        ...

    sync_head: '_SyncHead'
    workdir: '_Workdir'
    _workdir: Optional[str]

    path_index_sources: str
    path_index_binaries: str
    path_sync_head: str
    path_checkout: str
    path_pool: str
    path_root: str

    def _get_workdir(self) -> Optional[str]:
        ...

    def __init__(self, path: AnyPath):
        logger.debug(f'StockBase(path={path!r})')
        path_ = str_path(path)
        self.path_root = path_
        self.link_path = join(path_, 'link')

        self.name = basename(path_)
        if not exists(self.link_path):
            raise StockBase.StockBaseError(
                    f"stock link {self.link_path!r} doesn't exist")

        self.link = os.readlink(self.link_path)
        if not isdir(self.link):
            raise StockBase.StockBaseError(
                    f"stock link to non-directory `{self.link}'")


class StockPool(StockBase):
    """Class for managing a subpool-type stock"""

    def __init__(self,
                 path: AnyPath,
                 recursed_paths: Optional[list[str]] = None):
        logger.debug(
                f'StockPool(path={path!r}, recursed_paths={recursed_paths!r})')
        super().__init__(path)
        if recursed_paths is None:
            recursed_paths = []

        if self.link in recursed_paths:
            raise CircularDependency(
                f"circular dependency detected `{self.link}' is in recursed"
                f" paths {recursed_paths}"
            )

        self.pool = PoolKernel(self.link, recursed_paths)


class _Workdir:
    """Magical attribute for performing lazy evaluation of workdir.
    If workdir is False, we evaluate its value.
    """

    def __get__(self, obj: StockBase, type: Type[StockBase]) -> Optional[str]:
        if not obj._workdir:
            obj._workdir = obj._get_workdir()

        return obj._workdir

    def __set__(self, obj: StockBase, val: Optional[str]) -> None:
        obj._workdir = val


class _SyncHead:
    """Magical attribute.

    Set writes to the stock's HEAD.
    Get reads the value from it.
    """

    def __get__(self,
                obj: 'StockBase',
                type: Type['StockBase']) -> Optional[str]:
        path = obj.path_sync_head
        if exists(path):
            with open(path) as fob:
                fob.read().rstrip()

        return None

    def __set__(self, obj: 'StockBase', val: Optional[str]) -> None:
        path = obj.path_sync_head
        if val is None:
            if exists(path):
                os.remove(path)
        else:
            with open(path, 'w') as fob:
                fob.write(val + "\n")


class Stock(StockBase):
    """Class for managing a non-subpool-type stock."""

    sync_head = _SyncHead()

    def _get_workdir(self) -> str:
        """Return an initialized workdir path.

        If the stock links to a plain directory, the workdir is simply its
        path.

        If the stock links to a git repository, the workdir will point to a
        persistent lightweight checkout of the desired branch.
        """
        if not self.branch:
            return self.link

        orig = Git(self.link)
        checkout_path = self.path_checkout

        if not exists(checkout_path):
            mkdir(checkout_path)
            checkout = Git.init_create(checkout_path)
            checkout.set_alternates(orig)
        else:
            checkout = Git(checkout_path)

        def dup_branch(branch: str) -> None:
            # checkout latest changes
            commit = orig.rev_parse(branch.replace('%2F', '/'))
            if not commit:
                raise StockError(f"no such branch `{branch}' at {self.link}")
            checkout.update_ref("refs/heads/" + branch, commit)

        dup_branch(self.branch)
        checkout.checkout("-q", "-f", self.branch)

        if exists(join(checkout_path, "arena.internals")):
            dup_branch(self.branch + "-thin")

            command = f"cd {shlex.quote(checkout_path)} && sumo-open"
            error = os.system(command)
            if error:
                raise StockError("failed command: " + command)
            return join(checkout_path, "arena")

        # update tags
        for tag in checkout.list_tags():
            checkout.remove_tag(tag)

        for tag in orig.list_tags():
            try:
                v = orig.rev_parse(tag)
                assert v is not None
                checkout.update_ref("refs/tags/" + tag, v)
            except:  # TODO don't use bare except!
                continue

        return checkout_path

    _workdir: Optional[str]
    workdir = _Workdir()

    def _init_read_versions(self) -> dict[str, list[str]]:
        source_versions = {}
        for dpath, dnames, fnames in os.walk(self.path_index_sources):
            relative_path = relpath(dpath, self.path_index_sources)
            for fname in fnames:
                fpath = join(dpath, fname)
                with open(fpath) as fob:
                    versions = [line.strip() for line in fob if line.strip()]
                source_versions[join(relative_path, fname)] = versions
        return source_versions

    def __init__(self, path: AnyPath, pkgcache: PackageCache):
        StockBase.__init__(self, path)
        logger.debug(f'Stock(path={path!r}, pkgcache={pkgcache!r})')
        spath = join(str_path(path), '.pool')
        self.path_index_sources = join(spath, 'index-sources')
        self.path_index_binaries = join(spath, 'index-binaries')
        self.path_sync_head = join(spath, 'SYNC_HEAD')
        self.path_checkout = join(spath, 'CHECKOUT')
        self.path_pool = spath

        self.branch = None
        if "#" in self.name:
            self.branch = self.name.split("#")[1]

        self.source_versions = self._init_read_versions()
        self.workdir = None
        self.pkgcache = pkgcache

    def _sync_update_source_versions(self, directory: str) -> None:
        """update versions for a particular source package at <dir>"""
        logger.debug(f'Stock[name={self.name!r}]._sync_update_source_versions'
                     f'({directory=})')
        packages = deb_get_packages(directory)
        versions = verseek.list_versions(directory)

        relative_path = relpath(directory, self.workdir)
        source_versions_path = join(self.path_index_sources, relative_path)
        mkdir(source_versions_path)

        for package in packages:
            with open(join(source_versions_path, package), "w") as fob:
                for version in versions:
                    fob.write(version + '\n')

            self.source_versions[join(relative_path, package)] = versions

    def _sync_update_binary_versions(self, path: str) -> None:
        logger.debug(f'Stock[name={self.name!r}]._sync_update_binary_versions'
                     f'({path=})')
        binary_version_path = join(self.path_index_binaries,
                                   relpath(path, self.workdir))
        mkdir(dirname(binary_version_path))
        with open(binary_version_path, "w") as fob:  # create zero length file
            fob.truncate()

    def _sync(self, directory: Optional[str] = None) -> None:
        """recursive sync back-end.
        updates versions of source packages and adds binaries to cache"""
        logger.debug(f'Stock[name={self.name!r}]._sync(directory='
                     f'{directory!r})')

        directory = self.workdir if directory is None else directory
        assert directory is not None

        if isfile(join(directory, "debian/control")):
            return self._sync_update_source_versions(directory)

        for fname in os.listdir(directory):
            fpath = join(directory, fname)
            if not islink(fpath) and isfile(fpath) and \
                    splitext(fname)[1] in (".deb", ".udeb"):
                self.pkgcache.add(fpath)
                self._sync_update_binary_versions(fpath)

            if isdir(fpath):
                self._sync(fpath)

    @property
    def binaries(self) -> list[str]:
        """List package binaries for this stock ->
                            [ relative/path/foo.deb, ... ]"""
        relative_paths: list[str] = []
        for dpath, dnames, fnames in os.walk(self.path_index_binaries):
            for fname in fnames:
                fpath = join(dpath, fname)
                relative_paths.append(relpath(fpath, self.path_index_binaries))

        return relative_paths

    @property
    def sources(self) -> list[tuple[str, list[str]]]:
        """List package sources for this stock ->
                            [ (relative/path/foo, versions), ... ]"""
        return list(self.source_versions.items())

    def sync(self) -> None:
        """sync stock by updating source versions and importing binaries into
        the cache"""
        logger.debug(f'Stock[name={self.name!r}].sync()')
        if self.branch:
            if (Git(self.link).rev_parse(self.branch.replace('%2F', '/'))
                    == self.sync_head):
                return

        # delete old cached versions
        for path in (self.path_index_sources, self.path_index_binaries):
            if exists(path):
                shutil.rmtree(path)
                mkdir(path)

        self.source_versions = {}

        self._sync()

        if self.branch:
            self.sync_head = Git(self.path_checkout).rev_parse("HEAD")


class Stocks:
    """Class for managing and quering Pool Stocks in aggregate.

    Iterating an instance of this class produces all non-subpool type stocks.
    """

    def _load_stock(self, path_stock: AnyPath) -> None:
        logger.debug(f'loading stock from {path_stock}')
        stock: Optional[StockBase] = None
        try:
            stock = StockPool(path_stock, self.recursed_paths)
            self.subpools[stock.name] = stock.pool
        except CircularDependency:
            raise
        except (StockError, PoolError):
            pass

        if not stock:
            logger.info('trying from package cache...')
            try:
                stock = Stock(path_stock, self.pkgcache)
            except StockError:
                logger.warning(
                    'failed to get stock from package cache, ignoring...')
                return

        if stock:
            self.stocks[stock.name] = stock

    def _load_stocks(self) -> None:
        logger.debug('loading stocks')
        self.stocks: dict[str, StockBase] = {}
        self.subpools: dict[str, PoolKernel] = {}

        for stock_name in os.listdir(self.path):
            path_stock = join(self.path, stock_name)
            if not isdir(path_stock):
                logging.debug(f'ignoring non-stock {path_stock}')
                continue

            logging.info(f'loading {path_stock}')
            self._load_stock(path_stock)

    def __init__(self,
                 path: AnyPath,
                 pkgcache: PackageCache,
                 recursed_paths: Optional[list[str]] = None):
        if recursed_paths is None:
            recursed_paths = []
        self.path = path
        self.pkgcache = pkgcache
        self.recursed_paths = recursed_paths

        self._load_stocks()

    def reload(self) -> None:
        self._load_stocks()

    def __iter__(self) -> Iterator[StockBase]:
        # iterate across all stocks except subpools
        return (
            stock
            for stock in list(self.stocks.values())
            if not isinstance(stock, StockPool)
        )

    def __len__(self) -> int:
        return len(self.stocks) - len(self.subpools)

    @staticmethod
    def _parse_stock(stock: str) -> tuple[str, Optional[str]]:
        branch: Optional[str]
        try:
            dir, branch = stock.split("#", 1)
        except ValueError:
            dir = stock
            branch = None

        if branch:
            branch = branch.replace('/', '%2F')
        return abspath(dir), branch

    def register(self, stock_ref: str) -> None:
        logger.debug('Stocks.register')
        _dir, branch = self._parse_stock(stock_ref)
        logger.debug(f'parsed "{stock_ref}" -> _dir={_dir}, branch={branch}')
        if not isdir(_dir):
            raise PoolError(f"not a directory `{_dir}'")

        git: Optional[Git]
        try:
            git = Git(_dir)
        except GitError:
            git = None

        logger.debug(f'git = {git}')

        if ((not git and branch) or
                (git and branch and
                 not git.show_ref(branch.replace('%2F', '/')))):
            raise PoolError(f"no such branch `{branch}' at `{_dir}'")

        if git and not branch:
            ref_path = git.symbolic_ref("HEAD")
            branch = relpath(ref_path, 'refs/heads').replace('/', '%2F')
            logger.info(f'chose branch {branch}')

        stock_name = basename(abspath(_dir))
        if branch:
            stock_name += "#" + branch

        if stock_name in self.stocks:
            raise PoolError(
                f"stock already registered under name `{stock_name}'")

        stock_path = join(self.path, stock_name)
        Stock.create(stock_path, _dir)
        self._load_stock(stock_path)

    def unregister(self, stock_ref: str) -> None:
        dir, branch = self._parse_stock(stock_ref)
        stock_name = basename(dir)
        if branch:
            stock_name += "#" + branch

        matches: list[Stock] = []
        for stock in self.stocks.values():
            if realpath(stock.link) == realpath(dir):
                if not isinstance(stock, Stock):
                    logger.warning(f'stock {stock!r} incorrect type!')
                elif (not branch or stock.branch == branch):
                    matches.append(stock)

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
            # TODO this code is redundant as sumo no longer used
            checkout_path = stock.path_checkout
            if exists(join(checkout_path, "arena.internals")):
                command = f"cd {shlex.quote(checkout_path)} && sumo-close"
                error = os.system(command)
                if error:
                    raise PoolError("failed command: " + command)

            # remove cached binaries compiled from this stock
            blacklist: set[tuple[str, str]] = set()
            for path, versions in stock.sources:
                name = basename(path)
                blacklist |= set([(name, version) for version in versions])

            blacklist |= set(
                [parse_package_filename(basename(path))
                 for path in stock.binaries]
            )

            removelist = set(self.pkgcache.list()) & blacklist
            for name, version in removelist:
                self.pkgcache.remove(name, version)

        shutil.rmtree(stock.path_root)

    def sync(self) -> None:
        """sync all non-subpool stocks"""
        for stock in self:
            stock.sync()

    def get_source_path(self, name: str, version: str) -> Optional[str]:
        """Return path of source package"""
        for stock in self:
            for path, versions in stock.sources:
                if basename(path) == name and version in versions:
                    wd = stock.workdir
                    assert wd is not None
                    return join(wd, dirname(path))

        return None

    def exists_source_version(
            self,
            name: str,
            version: Optional[str] = None) -> bool:
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

    def get_subpools(self) -> list['PoolKernel']:
        return list(self.subpools.values())


@no_type_check
def sync(method):
    @no_type_check
    def wrapper(self, *args, **kws):
        if self.autosync:
            self.sync()
        return method(self, *args, **kws)

    return wrapper


class PoolKernel:
    """Class for creating and controlling a Pool.
    This class's public methods map roughly to the pool's cli interface"""

    PoolError = PoolError

    class Subpools:
        def __get__(
                self, obj: 'PoolKernel',
                type: Type['PoolKernel']
        ) -> list['PoolKernel']:
            return obj.stocks.get_subpools()

    subpools = Subpools()

    @staticmethod
    def parse_package_id(package: str) -> tuple[str, Optional[str]]:
        """Parse package_id string

        <package> := package-name[=package-version]

        Returns (name, version)
        Returns (name, None) if no version is provided
        """
        version: Optional[str]
        if "=" in package:
            name, version = package.split("=", 1)
        else:
            name = package
            version = None

        return name, version

    @staticmethod
    def fmt_package_id(name: str, version: Optional[str]) -> str:
        """Format package_id string -> string"""

        if version is None:
            raise PoolError("can't format package_id with unspecified version")

        return name + "=" + version

    def __init__(
            self,
            path: Optional[AnyPath] = None,
            recursed_paths: Optional[list[str]] = None,
            autosync: bool = True,
            debug: bool = False):
        """Initialize pool instance.

        if <autosync> is False, the user is expected to control syncing
        manually.
        """

        if recursed_paths is None:
            recursed_paths = []
        self.debug = debug

        if path is None:
            cwd = os.getcwd()
            path_env = os.getenv('POOL_DIR', cwd)
            if isdir(join(realpath(cwd), '.pool')):
                spath = cwd
            else:
                spath = path_env
        else:
            spath = str_path(path)

        spath = join(realpath(spath), '.pool')
        self.path_pkgcache = join(spath, 'pkgcache')
        self.path_stocks = join(spath, 'stocks')
        self.path_tmp = join(spath, 'tmp')
        self.path_build_root = join(spath, 'build/root')
        self.path_build_logs = join(spath, 'build/logs')
        self.path_build_info = join(spath, 'build/buildinfo')
        self.path_srcpkgcache = join(spath, 'srcpkgcache')

        self.full_path = spath
        self.path = dirname(spath)
        if not exists(spath):
            raise PoolError(f"no pool found (POOL_DIR={self.path})")

        self.buildroot = os.readlink(self.path_build_root)
        self.pkgcache = PackageCache(self.path_pkgcache)
        self.stocks = Stocks(
            self.path_stocks, self.pkgcache, recursed_paths + [self.path]
        )
        mkdir(self.path_tmp)
        self.autosync = autosync

    def register(self, stock: str) -> None:
        self.stocks.register(stock)

    def unregister(self, stock: str) -> None:
        self.stocks.unregister(stock)

    @sync
    def exists(self, package: str) -> bool:
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
    def _list(self, all_versions: bool,
              verbose: bool = False) -> list[tuple[str, str]]:
        """List packages in pool -> list of (name, version) tuples."""
        packages: set[tuple[str, str]] = set()
        for subpool in self.subpools:
            packages |= set(subpool._list(all_versions))

        packages |= set(self.pkgcache.list())
        for stock in self.stocks:
            for path, versions in stock.sources:
                package = basename(path)
                packages |= set([(package, version) for version in versions])

        if all_versions:
            return list(packages)

        newest: dict[str, str] = {}
        for name, version in packages:
            try:
                if name not in newest or \
                    debian_support.version_compare(
                            newest[name], version) < 0:
                    newest[name] = version
            except ValueError as e:
                if verbose:
                    print(f'Warning: skipping {name} {version} - {e}',
                          file=sys.stderr)
                else:
                    pass

        return list(newest.items())

    def list(self, all_versions: bool = False,
             verbose: bool = False) -> list[str]:
        """List packages in pool -> list of packages.

        If all_versions is True, returns all versions of packages,
        otherwise, returns only the newest versions.

        Will silently skip invalid debian version numbers, will show warning
        if verbose set.
        """
        return [
            self.fmt_package_id(name, version)
            for name, version in self._list(all_versions, verbose=verbose)
        ]

    # if this 'List' is replaced with 'list' it gives a type error here?!
    RS = TypeVar('RS', str, List[str])

    def resolve(self, unresolved: RS) -> RS:
        """Resolve a list of unresolved packages.
        If unresolved is a single unresolved package,
        return a single resolved package.

        If unresolved is a list of unresolved packages,
        return a list of resolved packages"""

        args: list[str]
        if isinstance(unresolved, str):
            args = [unresolved]
        else:
            args = unresolved

        packages = dict(self._list(all_versions=False))
        resolved = []

        for arg in args:
            name, version = self.parse_package_id(arg)
            logger.debug(f"resolve {name=} {version=}")
            if not version:
                if name not in packages:
                    raise PoolError(
                        f"can't resolve non-existent package `{name}'")
                version = packages[name]
            logger.debug(repr(packages))
            logger.debug(f"resolve {name=} {version=}")

            resolved.append(self.fmt_package_id(name, version))

        if isinstance(unresolved, str):
            return resolved[0]

        return resolved

    def _build_package_source(
            self,
            source_path: str,
            name: str,
            version: str,
            source: bool = False) -> None:

        build_outputdir = tempfile.mkdtemp(
            dir=self.path_tmp, prefix=f"{name}-{version}."
        )

        package = self.fmt_package_id(name, version)

        print("### BUILDING PACKAGE: " + package)
        print("###           SOURCE: " + source_path)

        # seek to version, build the package, seek back
        verseek.seek_version(source_path, version)
        args = []
        if self.debug:
            args.append('--preserve-build')
        if source:
            args.append('--build-source')
        with in_dir(source_path):
            command = ['deckdebuild', *args, self.buildroot, build_outputdir]
            print('# '+' '.join(command))
            error = subprocess.run(command).returncode
        verseek.seek_version(source_path)

        if error:
            msg = f"package `{package}' failed to build"
            if not self.debug:
                shutil.rmtree(build_outputdir)
                msg = f"{msg} - to preserve build dir, rerun with -d|--debug"
            else:
                msg = (f"{msg} - build dir preserved for debugging:"
                       f" {build_outputdir}")
            raise PoolError(msg)

        print()

        # copy *.debs and build output from output dir
        for fname in os.listdir(build_outputdir):
            fpath = join(build_outputdir, fname)
            fname_part, ext_part = splitext(fname)
            if splitext(fname)[1] in (".deb", ".udeb"):
                self.pkgcache.add(fpath)
            elif fname.endswith(".build"):
                shutil.copyfile(fpath, join(self.path_build_logs, fname))
            elif fname.endswith(".buildinfo"):
                shutil.copyfile(fpath, join(self.path_build_info, fname))
            elif ext_part in (".gz", ".xz", ".bz2") and \
                    splitext(fname_part)[1] == ".tar":
                shutil.copyfile(fpath, join(self.path_srcpkgcache, fname))

        shutil.rmtree(build_outputdir)

    @sync
    def getpath_deb(
            self,
            package: str,
            build: bool = True,
            source: bool = False) -> Optional[str]:
        """Get path to package in pool if it exists or None if it doesn't.

        By default if package exists only in source, build and cache it first.
        If build is False, we only return the path to packages in the cache.
        """
        name, version = self.parse_package_id(package)
        if version is None:
            raise PoolError(f"getpath_deb requires explicit version for"
                            f" `{package}'")

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
            raise PoolError(f"recently built package `{package}' missing"
                            " from cache")

        return path

    class BuildLogs(object):
        def __get__(
                self, obj: 'PoolKernel',
                type: Type['PoolKernel']) -> list[tuple[str, str]]:
            arr = []
            for fname in os.listdir(obj.path_build_logs):
                fpath = join(obj.path_build_logs, fname)
                if not isfile(fpath) or not fname.endswith(".build"):
                    continue

                log_name, log_version = fname[: -len(".build")].split("_", 1)
                arr.append((log_name, log_version))
            return arr

    build_logs = BuildLogs()

    def getpath_build_log(self, source_package: str) -> Optional[str]:
        """Returns build log of specific version requested.
        If no specific version is requested, returns build-log of latest
        version"""

        name, version = self.parse_package_id(source_package)
        log_versions = []

        def get_log_path(log_name: str, log_version: str) -> str:
            return join(self.path_build_logs,
                        f"{log_name}_{log_version}.build")

        for log_name, log_version in self.build_logs:
            if name == log_name:
                if version:
                    if version == log_version:
                        return get_log_path(name, version)
                else:
                    log_versions.append(log_version)

        if log_versions:
            log_versions.sort(debian_support.version_compare)  # type: ignore
            last_version = log_versions[-1]

            return get_log_path(name, last_version)

        for subpool in self.subpools:
            path = subpool.getpath_build_log(source_package)
            if path:
                return path

        return None

    @sync
    def gc(self,
           recurse: bool = True,
           verbose: bool = True) -> None:
        """Garbage collect stale data from the pool's caches"""

        whitelist: set[tuple[str, str]] = set()
        for stock in self.stocks:
            for path, versions in stock.sources:
                name = basename(path)
                whitelist |= set([(name, version) for version in versions])

            whitelist |= set(
                [parse_package_filename(basename(path))
                 for path in stock.binaries]
            )

        print(f'ignoring {len(whitelist)} whitelisted items')
        removelist = set(self.pkgcache.list()) - whitelist
        for name, version in removelist:
            if verbose:
                print(f'pkgcache: removing {name}={version}')
            self.pkgcache.remove(name, version)

        for stock in self.stocks:
            stock.sync_head = None

        if recurse:
            for subpool in self.subpools:
                subpool.gc(recurse)

    def drop_privileges(self, pretend: bool = False) -> bool:
        """Set the uid and gid of the current process to that of the pool.
        Returns whether or not we dropped privileges.

        if <pretend> is True, we don't actually drop privileges.
        """
        pool_uid = os.stat(self.full_path).st_uid
        pool_gid = os.stat(self.full_path).st_gid

        if os.getuid() != 0 or os.getuid() == pool_uid:
            return False

        if not pretend:
            os.setgid(pool_gid)
            os.setuid(pool_uid)
            importlib.reload(debfile)

        return True

    def sync(self) -> None:
        """synchronise pool with registered stocks"""
        self.stocks.sync()


def get_treedir(pkgname: str) -> str:
    if pkgname.startswith("lib"):
        return join(pkgname[:4], pkgname)
    else:
        return join(pkgname[:1], pkgname)


class Pool(object):
    PoolError = PoolError

    class PackageList:
        def __init__(self,
                     sequence: Optional[Iterable[str]] = None):
            self.inner = [] if sequence is None else list(sequence)
            self.missing: list[str] = []

        def __iter__(self):
            return iter(self.inner)

        def __iadd__(self, other):
            self.inner += other
            return self

        def append(self, pkg: str):
            self.inner.append(pkg)

        def sort(self, key, reverse: bool = False):
            self.inner.sort(key=key, reverse=reverse)

    parse_package_id = staticmethod(PoolKernel.parse_package_id)
    fmt_package_id = staticmethod(PoolKernel.fmt_package_id)

    @classmethod
    def init_create(
            cls: Type['Pool'],
            buildroot: AnyPath,
            path: Optional[AnyPath] = None) -> 'Pool':

        if path is None:
            cwd = os.getcwd()
            path = os.path.normpath(os.getenv('POOL_DIR', cwd))
            pool_path = join(realpath(path), ".pool")
            if not isdir(pool_path):
                path = cwd

        spath = join(realpath(str_path(path)), '.pool')
        path_pkgcache = join(spath, 'pkgcache')
        path_stocks = join(spath, 'stocks')
        path_tmp = join(spath, 'tmp')
        path_build = join(spath, 'build')
        path_build_root = join(spath, 'build/root')
        path_build_logs = join(spath, 'build/logs')
        path_build_info = join(spath, 'build/buildinfo')
        path_srcpkgcache = join(spath, 'srcpkgcache')

        if isdir(spath):
            raise PoolError("pool already initialized")

        if not isdir(buildroot):
            raise PoolError(f"buildroot `{buildroot}' is not a directory")

        mkdir(path_stocks)
        Git.set_gitignore(path_stocks, [
                'index-sources',
                'index-binaries',
                'SYNC_HEAD',
                'checkout'
        ])

        mkdir(path_pkgcache)
        Git.anchor(path_pkgcache)
        Git.set_gitignore(path_pkgcache, ["*.deb", "*.udeb"])

        mkdir(path_srcpkgcache)
        Git.anchor(path_srcpkgcache)
        Git.set_gitignore(path_srcpkgcache,
                          ["*.tar.xz", "*.tar.gz", "*.tar.bz2"])

        mkdir(path_build)

        mkdir(path_build_logs)
        Git.anchor(path_build_logs)
        Git.set_gitignore(path_build_logs, ["*.build"])

        mkdir(path_build_info)
        Git.anchor(path_build_info)
        Git.set_gitignore(path_build_info, ["*.buildinfo"])

        Git.set_gitignore(spath, ["tmp"])

        os.symlink(buildroot, path_build_root)

        return cls(path)

    def __init__(self,
                 path: Optional[AnyPath] = None,
                 debug: bool = False):
        kernel = PoolKernel(path, debug=debug)
        if kernel.drop_privileges(pretend=True):
            def f() -> PoolKernel:
                kernel.drop_privileges()
                return kernel

            # returns ObjProxy "pretending" to be a kernel, since we actually
            # want to pretend that it really is a kernel, we'll ask mypy to
            # play along
            kernel = cast('PoolKernel',
                          forked_constructor(f, print_traceback=True)())
        self.kernel = kernel

    def list(self, all_versions: bool = False,
             *globs: str, verbose: bool = False) -> 'Pool.PackageList':
        """List packages in pool (sorted) ->
                        Pool.PackageList (list + .missing attr)

        If no globs are specified, lists all packages.
        Globs that didn't match are listed in PackageList.missing
        """
        assert isinstance(all_versions, bool)

        def filter_packages(packages: list[str],
                            globs: list[str]) -> 'Pool.PackageList':
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

        packages = Pool.PackageList(self.kernel.list(all_versions,
                                                     verbose=verbose))
        if globs:
            packages = filter_packages(list(packages), list(globs))

        # TODO - unused code, should be completely removed...
        #def _cmp(a: str, b: str) -> int:
        #    a = Pool.parse_package_id(a)
        #    b = Pool.parse_package_id(b)
        #    return debian_support.version_compare(a[1], b[1])

        packages.sort(
                key=(lambda p:
                     debian_support.Version(Pool.parse_package_id(p)[1])),
                reverse=True)
        return packages

    def register(self, stock: str) -> None:
        self.kernel.register(stock)

    def unregister(self, stock: str) -> None:
        self.kernel.unregister(stock)

    def get(
                self, output_dir: str,
                packages: List[str], # as per above; 'list[]' here gives a
                                     # type error
                tree_fmt: bool = False,
                strict: bool = False,
                source: bool = False) -> 'Pool.PackageList':
        """get packages to output_dir -> resolved Pool.PackageList of packages

        If strict missing packages raise an exception,
        otherwise they are listed in .missing attr of the returned PackageList
        If debug, leave build chroot intact
        """

        self.kernel.autosync = False
        self.kernel.sync()

        resolved = Pool.PackageList()
        unresolved = []
        logger.debug('packages = ' + repr(packages))
        for package in packages:
            logger.debug("does " + str(package) + " exist?")
            if not self.kernel.exists(package):
                if strict:
                    raise PoolError(f"no such package ({package})")
                resolved.missing.append(package)
                continue

            if "=" in package:
                resolved.append(package)
            else:
                unresolved.append(package)

        if unresolved:
            resolved += self.kernel.resolve(unresolved)

        try:
            for package in resolved:
                raw_path_from = self.kernel.getpath_deb(package, source=source)
                path_from = raw_path_from if raw_path_from else ""
                fname = basename(path_from)

                if tree_fmt:
                    package_name = package.split("=")[0]
                    path_to = join(output_dir, get_treedir(package_name),
                                   fname)
                    mkdir(dirname(path_to))
                else:
                    path_to = join(output_dir, basename(path_from))

                if not exists(path_to):
                    hardlink_or_copy(path_from, path_to)
        finally:
            self.kernel.autosync = True

        return resolved

    def gc(self, recurse: bool = True) -> None:
        self.kernel.gc(recurse)
