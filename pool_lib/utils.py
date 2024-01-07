import sys
from typing import Optional, Callable, NoReturn

from . import PoolKernel, PoolError

err_msg = str | PoolError | FileNotFoundError


def warn(s: err_msg) -> None:
    print("warning: " + str(s), file=sys.stderr)


def fatal(msg: err_msg, help: Optional[Callable] = None) -> NoReturn:
    print("error: " + str(msg), file=sys.stderr)
    if help:
        help()
    sys.exit(1)


def read_packages(in_file: str, debug: bool = False) -> list[str]:
    packages = []
    try:
        with open(in_file, "r") as fob:
            for line in fob.readlines():
                line = line.split("#")[0].strip()
                if not line:
                    continue
                packages.append(line)
        return packages
    except FileNotFoundError as e:
        if not debug:
            fatal(e)
        else:
            raise


def pkgcache_list_versions(pool: PoolKernel, name: str) -> list[str]:
    versions = [
        pkgcache_version
        for pkgcache_name, pkgcache_version in pool.pkgcache.list()
        if pkgcache_name == name
        ]

    for subpool in pool.subpools:
        versions += pkgcache_list_versions(subpool, name)

    return versions
