from os.path import basename, dirname

from debian import debfile

from . import PoolKernel

PRE_RELEASE = ('alpha', 'beta', 'rc')


# pool info --registered
def print_registered(pool: PoolKernel) -> None:
    if pool.stocks:
        print("# stocks")
    print_stocks(pool)

    if pool.subpools:
        if pool.stocks:
            print()
        print("# subpools")
        print_subpools(pool)


# pool info --stocks
def print_stocks(pool: PoolKernel) -> None:
    for stock in pool.stocks:
        addr = stock.link
        if stock.branch:
            addr += "#" + stock.branch.replace('%2F', '/')
        print(addr)


# pool info --subpools
def print_subpools(pool: PoolKernel) -> None:
    for subpool in pool.subpools:
        print(subpool.path)


# pool info --build-root
def print_build_root(pool: PoolKernel) -> None:
    print(pool.buildroot)


# pool info --build-logs
def print_build_logs(pool: PoolKernel) -> None:
    for log_name, log_version in pool.build_logs:
        print(log_name + "=" + log_version)


# pool info --pkgcache
def print_pkgcache(pool: PoolKernel) -> None:
    pool.sync()
    for name, version in pool.pkgcache.list():
        print(name + "=" + version)


# support for pool info --stock-sources/--stock-binaries
def print_stock_inventory(stock_inventory: list[str]) -> None:
    package_width = max([len(vals[0]) for vals in stock_inventory])
    stock_name_width = max([len(vals[1]) for vals in stock_inventory])

    for package, stock_name, relative_path in stock_inventory:
        print(f"{package.ljust(package_width)}"
              f"  {stock_name.ljust(stock_name_width)}"
              f"  {relative_path}")


# pool info --stock-sources
def print_stock_sources(pool: PoolKernel) -> None:
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


# pool info --stock-binaries
def print_stock_binaries(pool: PoolKernel) -> None:
    pool.sync()

    stock_inventory = []
    for stock in pool.stocks:
        for path in stock.binaries:
            package = basename(path)
            relative_path = dirname(path)
            stock_inventory.append((package, stock.name, relative_path))

    if stock_inventory:
        print_stock_inventory(stock_inventory)
