Maintain a pool of packages from source and binary stocks
=========================================================

Introduction
------------

Pool is a system that maintains a pool of binary Debian packages which may
be either imported as-is from a registered collection of binaries, or
built on-demand from a registered source or collection of sources.

The dominant abstraction for the pool is a virtual filesystem folder
that you can get get specific versions of specific packages from. Behind
the scenes, the pool will build those binary packages from source if
required and cache the built binaries for future access.

Terminology / architecture
--------------------------

pool
   A pool of packages from source and binary "stocks".

stock
    a container for packages in binary or source form

stock types
    git single
        git repository containing one single package

    git
        git repository containing multiple packages

    plain
        regular directory containing multiple packages

    subpool
        another pool

binary
    a binary Debian package inside a stock

source
    Debian package source code - inside a stock

build root
    a chroot environment with an suitable tool-chain setup for building
    packages; e.g. https://github.com/turnkeylinux/buildroot

build logs
    the output from the build process for a package built from source

package cache
    a cache of binary packages either built from source or imported as-is

File/data structure
-------------------

All of pool's internals are neatly tucked out of sight in a special "hidden"
directory. The pool has no data formats/configuration files. All of its "data"
is stored directly as filesystem constructs::

    .pool/
        build/
            buildinfo/
                <package>_<version>_<arch>.buildinfo
                    # info about the build env
            root -> /path/to/buildroot
                # symbolic link
            logs/
                <package>_<version>.build
                    # log of the build process
           
        pkgcache/
            <package>_<version>_<arch>.deb
                # maybe in a pool-like tree
        
        srcpkgcache/
            <package>_<version>_<arch>.tar.gz
                # package source archive; requires --source switch

        stocks/
            <name>#<branch>/
                # if stock is git repo of package source
                link -> /path/to/stock
                    # symbolic link to the stock
                .pool/CHECKOUT
                    # local clone of git source branch
                .pool/SYNC_HEAD
                    # text file containing commit id of HEAD (full SHA)
                .pool/index-sources
                    <package>
                        # text file containing available package version/s (one
                        # version per line) - version/s calculated using
                        # 'autoversion'

Usage
-----

Syntax: pool <command> [options]

Maintain a pool of Debian packages from source

Commands:
    see below

    note: commands can be either separated with a space or a dash (as shown
          below)

Global options:
    -h, --help      show global/general help message and exit
                    - use '<command> --help' for command specific help

Environment variables::

    POOL_DIR        Location of pool (defaults to '.')
    POOL_LOG_LEVEL	Set log level for pool (no logging by default)
    DEBUG		    Global 'debug' log level (overrides 'POOL_LOG_LEVEL')

Initialize a new pool
'''''''''''''''''''''

pool-init /path/to/buildroot

Register a package stock into the pool
''''''''''''''''''''''''''''''''''''''

pool-register /path/to/stock[#branch]

Stock type can be:

* another pool (warning - watch out for circular dependencies)
* /path/to/git_repository[#branch]
* /path/to/regular_directory

Unregister a package stock from the pool
''''''''''''''''''''''''''''''''''''''''

pool-unregister /path/to/stock[#branch]

* only relevant content of .pool/stock is removed; cached packages in
  .pool/pkgcache are NOT removed
* cached packages can be removed by running a garbage collect - see 'pool-gc'

Print pool info
'''''''''''''''

pool-info [options]

Options::

  --registered      Prints list of registered stocks and subpools (default)
  --stocks          Prints list of registered stocks
  --subpools        Prints list of registered subpools

  --build-root      Prints build-root
  --build-logs      Prints a list of build logs for source packages

  --pkgcache        Prints list of cached packages
  --stock-sources   Prints list of package sources in registered stocks
  --stock-binaries  Prints list of package binaries in registered stocks

  -r, --recursive   Lookup pool info recursively in subpools

Print binary package build log
''''''''''''''''''''''''''''''

pool-info-get <package-name>

* no info if package hasn't been built
* error if package doesn't exist

Check if package exists in pool
'''''''''''''''''''''''''''''''

pool-exists package[=version]

Prints true/false if <package> exists in the pool.
If true exitcode = 0, else exitcode = 1
  
List packages in pool
'''''''''''''''''''''

pool-list [ "<package-glob>" ]

If <package-glob> is provided, print only those packages whose names
match the glob otherwise, by default, print a list of the newest
packages.

Options::

    -a --all-versions
        print all available versions of a package in the pool

    -n --name-only
        print only the names of packages in the pool (without the list)
            incompatible with -a option

* quoting <package-glob> is important to ensure that it is not expanded by the
  shell

Get packages from pool
''''''''''''''''''''''

pool-get [-options] <output-dir> [ package[=version] ... ]

If a package is specified without a version, get the newest package.
If no packages are specified as arguments, get all the newest packages.
Summary of success/failure of package/s is shown on completion.

Options::

  -i --input <file>     file from which we read package list (- for stdin)
                        - one package[=version] per line
  -s --strict           fatal error on missing packages
  -q --quiet            suppress warnings about missing packages
  -t --tree             output packages in a Debian apt repo like filesystem
                        tree

  -e, --preserve-buildroot-on-error
                        leave build chroot intact after build if failure (default)
  -p, --preserve-buildroot-always
                        always leave build chroot intact after build
  -n, --preserve-buildroot-never
                        never leave build chroot intact after build

  -o, --source          build source packages in addition to binary packages

Garbage collect stale cached data
'''''''''''''''''''''''''''''''''

pool-gc [ -options ]

Stale data includes:

A) A binary in the package cache that does not belong in any of the
   registered stocks.

   This includes binary packages which have since been removed from a
   registered stock.

B) Cached binary and source package versions.

Options::

  -R --disable-recursion    Disable recursive garbage collection of subpools

Example usage session
---------------------

::

    cd pools

    mkdir private
    cd private

    # initialize a new pool
    pool-init /chroots/rocky-build

    for p in /turnkey/projects/*; do
        # auto identifies the type of the stock we register
        pool-register $p
    done
        
    pool-info
        show pool information (registered containers, etc.)

    # woops, noticed I registered the wrong branch
    #  added #devel branch for emphasis - unregister would work without it
    #  since there is only one branch registered for that path
    pool-unregister /turnkey/projects/pool#devel

    # print a list of all packages in the pool (by name only)
    pool-list -n

    # print a list of all packages + newest versions
    pool-list

    # print a list of all packagse that match this glob
    pool-list turnkey-*

    # print a list of all package versions for neverland
    pool-list --all neverland

    # print a loooong list of all package versions, old and new, for all
    # packages
    #  watch out, every git commit in an autoversioned project is a new virtual
    #  version!
    pool-list --all

    for name in $(pool-list -n); do
        if ! exists -q $name; then
            echo "insane: package $name was just here a second ago"
        fi
    done

    mkdir /tmp/newest

    # get all the newest packages in the pool to /tmp/newest
    pool-get /tmp/newest 

    # get the newest neverland to /tmp/newest
    pool-get /tmp/newest neverland

    # get neverland 1.2.3 specifically to /tmp/newest
    pool-get /tmp/newest neverland=1.2.3

    # get all packages that are listed in product-manifest and exist in our
    # pool to /tmp/newest - don't warn us about packages which don't exist
    # (unsafe)
    pool-get /tmp/newest -q -i /path/to/product-manifest

    # creates a Debian apt repository like filesystem tree
    mkdir /tmp/product-repo
    for package in $(cat /path/to/versioned-product-manifest); do
        if pool-exists -q $package; then
            pool-get /tmp/product-repo --tree -s $package
        fi
    done
