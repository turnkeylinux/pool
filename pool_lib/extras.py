from typing import Optional, NoReturn

from debian import debfile, debian_support

from . import Pool, PoolKernel, PoolError, utils

PRE_RELEASE = ('alpha', 'beta', 'rc')


# binary2source dep
def extract_source_name(path: str) -> Optional[str]:
    deb = debfile.DebFile(path)
    if "Source" in deb.debcontrol():
        return deb.debcontrol()["Source"]
    return None


# pkgcache_getpath_newest dep
def pkgcache_list_versions(pool: PoolKernel, name: str) -> list[str]:
    versions = [
        pkgcache_version
        for pkgcache_name, pkgcache_version in pool.pkgcache.list()
        if pkgcache_name == name
        ]

    for subpool in pool.subpools:
        versions += pkgcache_list_versions(subpool, name)

    return versions


# pkgcache_getpath_newest dep
def has_pre_release(versions: list[str]) -> bool:
    for version in versions:
        for pre_release in PRE_RELEASE:
            if pre_release in version.lower():
                return True
    return False


# binary2source dep
def pkgcache_getpath_newest(pool: PoolKernel, name: str) -> Optional[str]:
    versions = pkgcache_list_versions(pool, name)
    if not versions:
        return None
    # Note this won't sort package pre-release & release versions properly
    # But it is the sort algorithm used by Debian...
    if has_pre_release(versions):
        utils.warn(f"pre-release version(s) found for {name} - version sorting"
                   " may be incorrect")
    versions.sort(key=debian_support.Version)
    version_newest = versions[-1]

    package = pool.fmt_package_id(name, version_newest)
    return pool.getpath_deb(package, build=False)


# getpath_build_log
def binary2source(pool: PoolKernel, package: str) -> Optional[str]:
    """translate package from binary to source"""
    name, version = pool.parse_package_id(package)
    if version:
        path = pool.getpath_deb(package, build=False)
        if not path:
            return None

        source_name = extract_source_name(path)
        if not source_name:
            return package

        return pool.fmt_package_id(source_name, version)

    # no version, extract source from the most recent binary
    path = pkgcache_getpath_newest(pool, name)
    if not path:
        return None

    source_name = extract_source_name(path)
    if not source_name:
        return name

    return source_name


def getpath_build_log(package: str, debug: bool = False) -> str | NoReturn:
    try:
        pool = Pool()
    except PoolError as e:
        #if not DEBUG:
        if not debug:
            utils.fatal(e)
        else:
            raise

    path = pool.kernel.getpath_build_log(package)
    if path:
        return path

    # maybe package is a binary name?
    # try mapping it to a source name and trying again

    source_package = binary2source(pool.kernel, package)
    if source_package:
        path = pool.kernel.getpath_build_log(source_package)

    if not path:
        package_desc = repr(package)
        if source_package:
            package_desc += f" ({source_package})"
        utils.fatal("no build log for " + package_desc)

    return path
