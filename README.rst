Maintain a pool of packages from source and binary stocks
=========================================================

Introduction
------------

The pool is a system thats maintains a pool of binary packages which may
be either imported as-is from a registered collection of binaries, or
built on-demand from a registered source or collection of sources.

The dominant abstraction for the pool is a virtual filesystem folder
that you can get get specific versions of specific packages from. Behind
the scenes, the pool will build those binary packages from source if
required and cache the built binaries for future access.

Terminology / architecture
--------------------------

pool
   The pool maintains a pool of packages from source and binary 'stocks'.

stock
    a container for packages in binary or source form

stock types
    git single
        git repository containing one single package

    git
        git repository containing multiple packages

    plain
        regular directory containing multiple packages

    sumo
        sumo arena containing multiple packages

    subpool
        another pool

binary
    a binary Debian package inside a stock

source
    a source Debian package inside a stock

build root
    a chroot environment with an suitable toolchain setup for building packages

build logs
    the output from the build process for a package built from source

package cache
    a cache of binary packages either built from source or imported as-is

File/data structure
-------------------

The pools tucks away all of its internals neatly out of site in a
'hidden' directory. The reason for doing this was to make it easy to
treat the pool as a 'special' directory, which may contain registered
stocks or subpools as sub-directories.

The pool has no data formats/configuration files. All of its 'data' is
stored directly as filesystem constructs::

    .pool/
        build/
            root -> /path/to/buildroot # symbolic link
            logs/
                <package>-<version>.build
                    log of the build process
           
        pkgcache/
            <package>-<version>.<arch>.deb # maybe in a pool-like tree
        
        stock/
            <name>#<branch>/
                link -> /path/to/stock # symbolic link to the stock
        
                source-versions/
                    <relative-path>/<package>
                        contains cached list of versions

                SYNC_HEAD # contains the last checkout/.git/HEAD we synced against
                checkout/

Usage
-----

Syntax: pool <command> [args]

Maintain a pool of packages from source and binary stocks

Environment variables::

    POOL_DIR            Location of pool (defaults to '.')
    DEBINFO_DIR         Location of debinfo cache (default: $HOME/.debinfo)
    POOL_ARCH           Architecture to 'pool get' for
                            - if not set, falls back to FAB_ARCH
                            - if FAB_ARCH not set, falls back to host arch
                            - see -a|--arch below for options

Initialize a new pool
'''''''''''''''''''''

pool-init /path/to/build-chroot

Register a package stock into the pool
''''''''''''''''''''''''''''''''''''''

pool-register /path/to/stock

Stock type can be:

* another pool (need to watch out for circular dependencies)
* /path/to/sumo_arena[#branch]
* /path/to/git_repository[#branch]
* /path/to/regular_directory

Unregister a package stock from the pool
''''''''''''''''''''''''''''''''''''''''

pool-unregstier /path/to/stock

Prints pool info
''''''''''''''''

pool-info [-options]

Options::

  --registered          Prints list of registered stocks and subpools (default)
  --stocks              Prints list of registered stocks
  --subpools            Prints list of registered subpools

  --build-root          Prints build-root
  --build-logs          Prints a list of build logs for source packages

  --pkgcache            Prints list of cached packages
  --stock-sources       Prints list of package sources in registered stocks
  --stock-binaries      Prints list of package binaries in registered stocks

  -r --recursive        Lookup pool info recursively in subpools

Prints source build log for package
'''''''''''''''''''''''''''''''''''

* info-build package 
    will return info on built package
        or no information if it wasn't built
        or an error that the package doesn't exist


Check if package exists in pool
'''''''''''''''''''''''''''''''

pool-exists package[=version]

Prints true/false if <package> exists in the pool.
If true exitcode = 0, else exitcode = 1

  
List packages in pool
'''''''''''''''''''''

pool-list [ <package-glob> ]

If <package-glob> is provided, print only those packages whose names
match the glob otherwise, by default, print a list of the newest
packages.

Options::

    -a --all-versions
        print all available versions of a package in the pool

    -n --name-only
        print only the names of packages in the pool (without the list)
            incompatible with -a option

Get packages from pool
''''''''''''''''''''''

pool-get [-options] <output-dir> [ package[=version] ... ]

If a package is specified without a version, get the newest package.
If no packages are specified as arguments, get all the newest packages.

Options::

  -i --input <file>     file from which we read package list (- for stdin)

  -s --strict           fatal error on missing packages
  -q --quiet            suppress warnings about missing packages

  -t --tree             output dir is in a package tree format (like a repository)

  -a|--arch ARCH        Architecture tp build for - overrides POOL_ARCH
                            - package(s) being built must support ARCH
                            - must be of:
                                'amd64' - supported on amd64 host only
                                'arm64' - supported on amd64 or arm64 host
                                'all'   - supported on amd64 or arm64 host
                                'any'   - on arm64 host; will only build arm64 pkgs



Garbage collect stale data from the pool's caches
'''''''''''''''''''''''''''''''''''''''''''''''''

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

    #  woops, noticed I registered the wrong branch
    #  added #devel branch for emphasis 
    #  unregister would work without it since there is only one branch registered for that path
    pool-unregister /turnkey/projects/pool#devel

    # prints a list of all packages in the pool (by name only)
    pool-list -n

    # prints a list of all packages + newest versions
    pool-list
      
    # prints a list of all packagse that match this glob
    pool-list turnkey-*

    # prints a list of all package versions for neverland
    pool-list --all neverland

    # prints a loooong list of all package versions, old and new, for all packages
    # watch out, every git commit in an autoversioned project is a new virtual version
    pool-list --all

    for name in $(pool-list -n); do
        if ! exists -q $name; then
            echo insane: package $name was just here a second ago
        fi
    done

    mkdir /tmp/newest

    # gets all the newest packages in the pool to /tmp/newest
    pool-get /tmp/newest 

    # gets the newest neverland to /tmp/newest
    pool-get /tmp/newest neverland

    # gets neverland 1.2.3 specifically to /tmp/newest
    pool-get /tmp/newest neverland=1.2.3

    # gets all packages that are listed in product-manifest and exist in our pool to /tmp/newest
    # don't warn us about packages which don't exist (unsafe)
    pool-get /tmp/newest -q -i /path/to/product-manifest

    # creates a repository like 
    mkdir /tmp/product-repo
    for package in $(cat /path/to/versioned-product-manifest); do
        if pool-exists -q $package; then
            pool-get /tmp/product-repo --tree -s $package
        fi
    done
