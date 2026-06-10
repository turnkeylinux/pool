Maintain a pool of packages from source and binary stocks
=========================================================

Introduction
------------

Pool is a system that maintains a pool of binary Debian packages which may be
either imported as-is from a registered collection of binaries, or built
on-demand from a registered source or collection of sources.

The dominant abstraction for the pool is a virtual filesystem folder that
supports getting specific versions of specific packages. Behind the scenes, the
pool will build those binary packages from source if required (and source is
registered) and cache the built binaries for future access.

Terminology / architecture
--------------------------

Pool:
    A pool of packages from source and binary "stocks".

Stock:
    A directory containing the source of package/s (not necessarily package
    source code).

Stock types:
    Git single:
        Git repository containing one single package.
    Git:
        Git repository containing multiple packages.
    Plain:
        Regular directory containing multiple packages.
    Sub-pool:
        Another pool.

Binary:
    A pre-built binary Debian package (aka deb file) inside a stock.

Source:
    Debian package source code - i.e. directory containing source code and a
    debian/ subdirectory - inside a stock.

Buildroot:
    A chroot environment with an suitable tool-chain set up for building
    packages; e.g. https://github.com/turnkeylinux/buildroot

Build logs:
    The output from the build process for a package built from source.

Package cache:
    A cache of binary packages either built from source or imported as-is.

File/data structure
-------------------

The pool has no data formats/configuration files. All of its "data" is stored
directly as filesystem constructs within a "hidden" directory::

    .pool/
    |-- build/
    |   |-- buildinfo/
    |   |   `-- <binary_package_name>_<version>_<arch>.buildinfo
    |   |       # info about the build env
    |   |-- root -> /path/to/buildroot
    |   |   # symbolic link
    |   `-- logs/
    |       `-- <binary_package_name>_<version>.build
    |           # log of the build process
    |-- pkgcache/
    |   `-- <binary_package_name>_<version>_<arch>.deb
    |       # maybe in a pool-like tree
    |-- srcpkgcache/
    |   `-- <binary_package_name>_<version>_<arch>.tar.gz
    |       # package source archive; requires --source switch
    `-- stocks/
        `-- <name>#<branch>/
            |   # if stock is git repo of package source
            |-- link -> /path/to/stock
            |   # symbolic link to the stock
            |-- CHECKOUT
            |   # local clone of git source branch
            |-- SYNC_HEAD
            |   # text file containing commit id of HEAD (full SHA)
            `-- index-sources
                `-- <binary-package-name>
                    # text file containing available package version/s (one
                    # version per line) - version/s calculated using
                    # 'autoversion'

Usage
-----

Syntax: pool <command> [options]

Maintain a pool of Debian packages from source

Note that commands can be either separated with a space or a dash.

Global options:
    -h, --help      show global/general help message and exit
                    - use '<command> --help' for command specific help

Environment variables::

    POOL_DIR        Location of pool (defaults to '.')
    POOL_LOG_LEVEL	Set log level for pool (no logging by default)
    DEBUG		    Global 'debug' log level (overrides 'POOL_LOG_LEVEL')

Initialize a new pool
'''''''''''''''''''''

Create a pool capable of building packages from source::

    pool-init /path/to/buildroot

Create a pool that only supports plain and sub-pool stocks::

    pool-init --no-buildroot

Register a package stock into the pool
''''''''''''''''''''''''''''''''''''''

Make package stocks available::

    pool-register /path/to/stock[#branch]

A stock type can be:
- /path/to/git_repository[#branch]
- /path/to/regular_directory
- another pool (warning - watch out for circular dependencies)

Unregister a package stock from the pool
''''''''''''''''''''''''''''''''''''''''

Remove stock::

    pool-unregister /path/to/stock[#branch]

Note: Only the relevant content of .pool/stock is removed; cached packages in
      .pool/pkgcache are NOT removed. Cached packages can be removed by running
      a garbage collect - see 'pool-gc'

Print pool info
'''''''''''''''

Get info about package stocks and other pool config::

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

Get build log of specific package::

    pool-info-get <package-name>

No info if package hasn't been built. Error if package doesn't exist.

Check if package exists in pool
'''''''''''''''''''''''''''''''

Simple check of package availability::

    pool-exists package[=version]

Prints true/false if <package> exists in the pool. The exitcode matches the
status; 0 if True, else 1.
  
List packages in pool
'''''''''''''''''''''

List some/all packages - and their versions::

    pool-list [ "<package-glob>" ]

By default all packages and their latest version are displayed. If
<package-glob> is provided, only the matching packages are returned.

Options::

    -a --all-versions
        print all available versions of a package in the pool

    -n --name-only
        print only the names of packages in the pool (without the list)
            incompatible with -a option

Quoting <package-glob> is important to ensure that it is not expanded by the
shell.

Use --all-versions with caution when numerous git stocks are registered. Pool
considered every commit as a virtual version so the output may be very large.

Get packages from pool
''''''''''''''''''''''

Get package/s from registered stock/s::

    pool-get [-options] <output-dir> [ package[=version] ... ]

If a package is specified without a version, get the newest package. If no
packages are specified as arguments, get all the newest packages. Summary of
success/failure of package/s is shown on completion.

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

Clean pool's package cache::

    pool-gc [ -options ]

Stale data includes:

A) A binary in the package cache that does not belong in any of the registered
   stocks.

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
    pool-init /chroots/my_buildroot

    for pkg in /turnkey/projects/*; do
        # auto identifies the type of the stock we register
        pool-register $pkg
    done
    
    # show pool information including registered stocks, etc.
    pool-info

    # woops, accidentally registered the wrong branch - added #devel branch for
    # emphasis - unregister would work without it since there is only one
    # branch registered for that path
    pool-unregister /turnkey/projects/pool#devel

    # print a list of all packages in the pool (by name only)
    pool-list -n

    # print a list of all packages + newest versions
    pool-list

    # print a list of all packages that match this glob
    pool-list "turnkey-*"

    # print a list of all package versions for package named neverland
    pool-list --all neverland

    # print a loooong list of all package versions, old and new, for all
    # packages
    pool-list --all

    for name in $(pool-list -n); do
        if ! pool-exists -q "$name"; then
            echo "insane: package $name was just here a second ago"
        fi
    done

    # get all the newest packages in the pool to /tmp/newest
    mkdir /tmp/newest
    pool-get /tmp/newest 

    # get the latest neverland package into /tmp/newest
    pool-get /tmp/newest neverland

    # get neverland 1.2.3 specifically to /tmp/newest
    pool-get /tmp/newest neverland=1.2.3

    # get all packages that are listed in product-manifest and exist in our
    # pool to /tmp/newest - don't warn us about packages which don't exist
    # (unsafe)
    pool-get /tmp/newest -q -i /path/to/product-manifest

    # create a Debian apt repository like filesystem tree
    mkdir /tmp/product-repo
    for package in $(cat /path/to/versioned-product-manifest); do
        if pool-exists -q "$package"; then
            pool-get /tmp/product-repo --tree -s $package
        fi
    done
