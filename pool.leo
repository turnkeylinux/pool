<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="0" clone_windows="0"/>
<globals body_outline_ratio="0.488082901554">
	<global_window_position top="0" left="500" height="965" width="770"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="loni.20100827184947" a="E"><vh>Project</vh>
<v t="loni.20100827184947.1" a="E"><vh>design</vh>
<v t="loni.20100827184947.2"><vh>brainstorming</vh>
<v t="zaril.20100828060043"><vh>first draft</vh></v>
</v>
<v t="zaril.20100828055849"><vh>terminology</vh></v>
<v t="loni.20100827184947.4"><vh>file/data structure</vh></v>
<v t="loni.20100827184947.5"><vh>cli syntax</vh></v>
<v t="loni.20100827184947.6"><vh>usage examples</vh></v>
</v>
<v t="loni.20100827184947.7" a="E"><vh>implementation</vh>
<v t="zaril.20100906050211"><vh>implement full command set for binaries in regular directories</vh>
<v t="zaril.20100906050211.1"><vh>init /path/to/build-chroot</vh></v>
<v t="zaril.20100906050211.2"><vh>register / unregister # regular directories</vh></v>
<v t="zaril.20100906230204"><vh>info</vh></v>
<v t="zaril.20100906050211.4"><vh>exists</vh>
<v t="zaril.20100907030232"><vh>refactor away stock</vh></v>
</v>
<v t="zaril.20100906050211.5"><vh>list</vh></v>
<v t="zaril.20100906050211.6"><vh>get</vh></v>
</v>
<v t="zaril.20100909033533"><vh>pool contains pool</vh></v>
<v t="zaril.20100910205006"><vh>BUG: sync not importing binaries?</vh></v>
<v t="zaril.20100909050527" a="E"><vh>support regular sources in regular directories</vh>
<v t="zaril.20100911052023" a="M"><vh>setup a local caching proxy</vh>
<v t="zaril.20100912044439" a="M"><vh>fix squid</vh></v>
<v t="zaril.20100912052909"><vh>configure jaunty to use apt-proxy</vh></v>
<v t="zaril.20100912065617"><vh>apt-proxy README</vh></v>
<v t="zaril.20100912052439"><vh>test debootstrap with caching proxy</vh></v>
</v>
<v t="zaril.20100910021430" a="M"><vh>research existing solutions</vh>
<v t="zaril.20100910040422.2" a="M"><vh>explore cowdancer</vh></v>
<v t="zaril.20100911012707" a="M"><vh>explore fl-cow</vh></v>
<v t="zaril.20100912055420" a="M"><vh>exlore apt-move</vh></v>
<v t="zaril.20100911004946"><vh>explore pbuilder</vh>
<v t="zaril.20100918092126"><vh>alternatives</vh></v>
</v>
<v t="zaril.20100916032546" a="M"><vh>explore build dependencies</vh></v>
<v t="zaril.20100911091317"><vh>research suid</vh></v>
</v>
<v t="zaril.20100923043734" a="M"><vh>exists</vh></v>
<v t="zaril.20100923071058" a="TV"><vh>list</vh></v>
</v>
</v>
</v>
</vnodes>
<tnodes>
<t tx="loni.20100827184947">@nocolor
</t>
<t tx="loni.20100827184947.1"></t>
<t tx="loni.20100827184947.2">* IDEAS
change untagged auto-versioning to always be smaller than tagged autoversioning

auto-versioning a separate program?
    this way we could re-use the code for pyproject's auto-versioning

leave failed builds in temporary directory
    so we can diagnose problem manually

    $TMPDIR/pool/&lt;poolname&gt;/&lt;package&gt;

figure out how to allow packages to be built manually
    unversioned - for testing?

* QUESTIONS
Q: what should we call the system?
A:
    binpool
        pool of binaries
        separate `srcpool' system will need to be developed later to comply with licensing restrictions

---
Q: do we need a binary cache for the versions information? (e.g., SQLite)
A:

probably not - don't worry about performance until after you have benchmarks 
    not sure it matters
    premature optimization is the root of all evil

ideal solution - figure out how to store the information directly in the filesystem
    format should be simple and easy to access

---
INSIGHT: debian package can not contain another debian package so scanning containers is a shallow, quick
operation
---
Q: how does auto-versioning for Sumo arena work?
GOTCHA: sumo auto-versioning is tricky
	is the number of commits the same on different fat branches?
	
	GOTCHA: fat thin commits don't actually include directory modifications

    IDEAS:
        maybe we only count commits on thin branch?
        maybe only count overlays as revisions?
            logic would then be very similar to Git repo logic
    
            what happens if we apply a patch to the fat?
                shouldn't that auto-increment?
        manual incrementation of auto-version?
    
---
Q: how does auto-versioning work for multi-debian packagse in a regular Git repository?
---
Q: do we support different versioning for single-debian package and multi-debian packages?
    </t>
<t tx="loni.20100827184947.4">FILE/DATA STRUCTURE

.pool/
    build/
        root -&gt; /path/to/buildroot # symbolic link
        logs/
            &lt;package&gt;-&lt;version&gt;.build
                log of the build process
       
    pkgcache/
        &lt;package&gt;-&lt;version&gt;.&lt;arch&gt;.deb # maybe in a pool-like tree
    
    stock/
        &lt;name&gt;#&lt;branch&gt;/
            link -&gt; /path/to/stock # symbolic link to the stock
            HEAD # contains the last HEAD we've we handled
    
            &lt;relative-path&gt;/&lt;package&gt;.versions
                contains cached list of versions
    
    



    </t>
<t tx="loni.20100827184947.5">=== ENVIRONMENT

    POOL_DIR        defaults to cwd
    POOL_TMPDIR     defaults to TMPDIR or /var/tmp

=== CLI SYNTAX

* init /path/to/build-chroot
    initialize a new pool

* register /path/to/stock
    register a package stock with the pool
    stock type can be:
        another pool
            (need to watch out for circular dependencies)
        /path/to/sumo_arena[#branch]
        /path/to/git_repository[#branch]
        /path/to/regular_directory

* unregister stock
    unregister a stock from the pool

* info
    show pool information (registered stock, etc.)

* get [-options] /path/to/output/dir [ package[=version] ... ]
    function
        retrieve requested packages to output dir
            if a specific package version is requested, get that
            if a specific version is not requested, retrieve the newest version
    
        if no packages are requested, output all the newest packages
    
    psuedo-logic for getting a single package=version
        update binary cache 
            scan all stock deltas for new binary packages to put into our cache
        if lookup package in binary cache:
            return package
        
        update source versions
            scan all stock deltas for new debian source packages
                a debian package cannot be inside another debian package
            scan control file to get package name list and generate new auto-versions
            output new auto-versions into pool's versions cache
    
        lookup stock, relative_path for requested package=version in version cache
        recalculate commit-id for stock, check that version is legal
        seek to commit, extract source for debian package
        build source for debian package in build environment
        insert built packages into binary cache
    
    options
        -t --tree
            output dir is in package tree format (like an automatic repository)
                $outputdir/n/neverland/neverland-&lt;version&gt;.&lt;arch&gt;.deb
    
            instead of
                $outputdir/neverland-&lt;version&gt;.&lt;arch&gt;.deb
    
        -s --strict
            fatal error on missing packages 
                by default we just issue warnings (which can be suppressed with -q)
                the reason this is the default is that:
                a) this what analogous tools such as mv and cp do when given multiple broken sources to copy/move
                b) easy things should be easy, hard things should be possible
                    given a manifest of packages from multiple pools (e.g., private world), 
                    we can ask each pool to give us the portion of packages it holds for that manifest
                    without having to first determine in which pool a package is located
    
        -q --quiet
            suppress warnings about missing packages
    
        -i &lt;file&gt; | -
            file from which we read the list of packages to retrieve

        IDEA: --symbolic get? copy as links instead of real files?
            will that still work?
    
* list [ &lt;package-glob&gt; ]
    if &lt;package-glob&gt; is provided, print only those packages whose names match the glob
    otherwise, by default, print a list of the newest packages

    -a --all-versions
        print all available versions of a package in the pool

    -n --name-only
        print only the names of packages in the pool (without the list)
            incompatible with -a option

* exists package[=version]
    prints true/false if the package exists in the pool
    if true exitcode = 0, false = 1

FUTURE
    register-block /path/to/stock package[=version]
        register a block on a specific package inside a specific stock
            this blocks the package from being included in the pool

    unregister-block /path/to/stock package[=version]
        unregister the block

    open
        open the FUSE-based filesystem representation of the pool

    close
        close the FUSE-based filesystem representation of the pool</t>
<t tx="loni.20100827184947.6"># all commands are specified without the toolkit prefix
# I haven't yet decided for sure what the name of this tool will be

cd pools

mkdir private
cd private

init /chroots/rocky-build
    initialize a new pool

register /turnkey/projects/*
    auto identifies the type of the stock we register
    e.g., if its a 
        /path/to/sumo_arena[#branch]
        /path/to/git_repository[#branch]
        /path/to/regular_directory

info
    show pool information (registered containers, etc.)

unregister /turnkey/projects/covin#devel
    woops, noticed I registered the wrong branch
        added #devel branch for emphasis 
        unregister would work without it since there is only one branch registered for that path

list -n
    prints a list of all packages in the pool (by name only)

list
    prints a list of all packages + newest versions

list turnkey-*
    prints a list of all packagse that match this glob

list --all neverland
    prints a list of all package versions for neverland

list --all
    prints a loooong list of all package versions, old and new, for all packages
        watch out, every git commit in a Sumo arena is a new virtual version

for name in $(list -n); do
    if ! exists -q $name; then
        echo insane: package $name was just here a second ago
    fi
done

mkdir /tmp/newest

get /tmp/newest 
    gets all the newest packages in the pool to /tmp/newest

get /tmp/newest neverland
    gets the newest neverland to /tmp/newest

get /tmp/newest neverland=1.2.3
    gets neverland 1.2.3 specifically to /tmp/newest

get /tmp/newest -q -i /path/to/product-manifest
    gets all packages that are listed in product-manifest and exist in our pool to /tmp/newest
    don't warn us about packages which don't exist (unsafe)

# creates a repository like 
mkdir /tmp/product-repo
for package in $(cat /path/to/versioned-product-manifest); do
    if exists -q $package; then
        get /tmp/product-repo --tree -s $package
    fi
done</t>
<t tx="loni.20100827184947.7">ROADMAP
support Git repositories
    scan deltas since last scan
support Sumo arenas</t>
<t tx="zaril.20100828055849">pool
    a system for which maintains a pool of binary packages built on-demand from registered stock

stock
    a container for packages in binary or source form

build root
    a chroot environment with an suitable toolchain setup for building packages</t>
<t tx="zaril.20100828060043">Q: how do i name this project?

alternatives
    pms (package management system), and you know what else...
    tklps (TurnKey Linux Packaging System)
    spkg (turnkey package ...) - used by slackware
    repoware (repository software)
    poolman (pool management software)
    
A: poolman
    it is the software that manages our pool of packages, see objectives

----

Q: should we have seperate reps per release?
A:  easier to manage
    different toolchain for different releases, poolman also handles the building of packages
    different releases generally mean major updates
    this can be transparent to fab
    smaller global pool, not inifinate in size
    we can retire / archive older release pools
    A: yes

----

Q: what do i call the action/outcome of passing a manifest to poolman?

IDEA: time travel
      a release has a life span, and we can travel forward and backwards on the timeline

action
    travel
    visit
    move
    pluck
    checkout
    peak
    seek
    commit
    make
    generate*
    branch
    
outcome
    instance*
    state
    period
    entity
    frame
    snapshot

latest?
    latest
    present
    head
    current


A: the action is to generate, the outcome is an instance.</t>
<t tx="zaril.20100906050211"></t>
<t tx="zaril.20100906050211.1">initialize a new pool

* init /path/to/build-chroot
    initialize a new pool

* logic
    mkdir .pool/{build,binaries,sources}
    mkdir .pool/build/logs
    link .pool/build to buildroot

</t>
<t tx="zaril.20100906050211.2">* register /path/to/stock
    register a package stock with the pool
    stock type can be:
        another pool
            (need to watch out for circular dependencies)
        /path/to/sumo_arena[#branch]
        /path/to/git_repository[#branch]
        /path/to/regular_directory


rescanned every time
    we can't tell if they've changed
no auto-versioning

* register logic
    raise exception if stock is already registered
    if it isn't, register stock by
        creating stock/&lt;stock_name&gt;
        creating symbolic link
            ln -s &lt;dir&gt; stock/&lt;stock_name&gt;/path

* unregister logic
    raise "stock not registered" exception if  dir doesn't match stock/path
    rmdir .pool/stock/name
    </t>
<t tx="zaril.20100906050211.4">TESTS: 
    register a directory with one binary package
    register another directory with two more packages

cli syntax
    exists package[=version]
        prints true/false if the package exists in the pool
        if true exitcode = 0, false = 1
    
logic
    sync pool with the registered stocks
    check if any binaries exist

sync logic
    search all registered stocks recursively for binary packages
    if we find a new package (that we don't already have)
        hardlink/copy into cache
    

    </t>
<t tx="zaril.20100906050211.5">* list [ &lt;package-glob&gt; ]
    if &lt;package-glob&gt; is provided, print only those packages whose names match the glob
    otherwise, by default, print a list of the newest packages

    -a --all-versions
        print all available versions of a package in the pool

    -n --name-only
        print only the names of packages in the pool (without the version)
            incompatible with -a option</t>
<t tx="zaril.20100906050211.6">logic
    if no arguments, list the newest packages

    check if package exists
        raise error if it doesn't and we're strict
        warn if we're not strict unless we're quiet

    for each package:
        if tree mode:
            calc treedir (outputdir+...)
            mkdir -p treedir

        ask the pool to output that package to the outputdir


    </t>
<t tx="zaril.20100906230204">* logic
    list .pool/stock subdirectories
    for each stock:
        print its path
</t>
<t tx="zaril.20100907030232">class PoolStocks:
    def __init__(self):
        pass

</t>
<t tx="zaril.20100909033533">ROADMAP
    solve typing issue
    proxy all pool functions
    handle circular dependencies

Q: how do we `identify' pools?
A:
    try to initialize pool object at link path?
        otherwise its a regular directory
---
Q: how do I prevent cyclic subpools?
A:
    track recursed_paths. Prevent 
</t>
<t tx="zaril.20100909050527">* ROADMAP
exists
list
get

* TEST:
    add debian package (buildable)
    link to real buildroot

* IDEAS
get_sources
    path/to/dir/package-name: &lt;version&gt;

add all legally listed binary packages files we build to cache
    (so we don't have to rebuild the same package multiple times)

extract package to package build directory
    
we need to install build dependencies to the buildroot  
    with apt-get
   </t>
<t tx="zaril.20100910021430">
* TODO
explore building packages with pbuilder
    Q: does pbuilder need root privileges?
    Q: can we use fakeroot?
    Q: how does pbuilder work?

</t>
<t tx="zaril.20100910040422.2">SUMMARY

how it works
    LD_PRELOAD trick
    directory needs to be scanned by cow-shell command
    hardlinks are always broken
    supports a pbuilder backend

usage
    cp -al src dst
    cd dst &amp;&amp; cow-shell
        file hardlinked - wil be copied to a new file before write

usage with chroot
    cow-shell invoked inside chroot.
        e.g. chroot /path/to/chroot cow-shell command-to-execute


* RESOURCE: http://blog.wiz.ro/articles/Building%20Debian%20packages%20with%20cowbuilder.pod
    explains how to use cowbuilder variant of pbuilder

cowdancer is copy-on-write upon directory trees copied with cp -la

pdebuild --pbuilder cowbuilder 


    </t>
<t tx="zaril.20100910205006"></t>
<t tx="zaril.20100911004946">Q: does the pbuilder environment setup mounts?

TODO
    read manual
    experiment with pbuilder as is
    hack it to support deck

SUMMARY

an option for saving the chroot environment instead of deleting it afterwards

pbuilder is a file year old program

its possible to run pdebuild with sudo
    
but creating the pbuilder environment requires root privileges

how does it work?
    unpacks a tarball
    install build dependencies
    gains privileges with fakeroot
        doesn't have to be real root
    builds package
    

pbuilder needs root privileges to work

uses cdebootstrap instead of debootstrap (bydefault)

by default, only supports one build environment at a time
    you can specify --basetgz option though

build dependencies need to be installed non-interactively
    some packages don't install non-interactively

debian sweeps package with pbuilder

some builds don't finish in a finite time?

sbuild - perl script
    used in buildd system
    parses Build-Depends
    perform various checks
        includes many hacks to get thsi to build
        table of which packages to substitute for virtual packages


IDEAS
    reimplement pbuilder concepts with deck

	
INSIGHT: cowdancer is not secure for isolation purposes
    hardlinks could be modified


RESOURE: http://apsy.gse.uni-magdeburg.de/main/index.psp?page=hanke/pbuilder-ssh&amp;lang=en

pbuilder-ssh: remote front-end for pbuilder
    not part of the distribution

RESOURCE: pbuilder User manual (in /usr/share/doc/pbuilder)

pbuilder doesn't try to guess what the package needs

    if a choice is to be made - tries to make the worst choice

pbuilder create
    create base chroot image with debootstrap
    --distribution 
</t>
<t tx="zaril.20100911012707">same principle as cowdancer, slightly different implementation

fl-cow will apply to any directory inside FLCOW_PATH

</t>
<t tx="zaril.20100911052023">* SUMMARY
what is this good for?
    we don't want to retrieve build dependencies over the network over and over again
        IDEA: patch apt-proxy so it doesn't hang if it can't retrieve a new Packages/Sources
        
    debootstrap of build roots

two types of proxies
    general (squid)
    application specific (apt-proxy, apt-cacher, approx)

which to choose
    apt-proxy
        pros
            standard, featureful, mature
            known to work with most programs
            can be easily changed
            works inside chroot
            supports decoupling of backend/frontend (also true for approx)
                with multiple redundant backends
            supports remote python console for debugging

            comes preconfigured with backends for debian, security , ubuntu and ubuntu-security

        cons
            bloat?

privileges required
    apt-proxy runs as aptproxy
    approx runs as user approx
    apt-cacher runs as www-data
    approx, wants root?

squid
    useful for non-Debian uses (e.g., Sumo)
    configure in apt.conf via http::proxy variable
        http://[[user][:pass]@]host[:port]/

    gotcha - you don't want to ignore no-caching options
        we need it for some files (e.g., archive files - Packages)

    cons - complex configuration

apt-proxy       Debian archive proxy and partial mirror builder
    now in version 2 (looks redesigned)
        v1 was written in shell script
        rewritten in python by 'rany' (Manuel Estrada Sainz)
            died in tragic car accident

    most complex program

    known to work with
        debootstrap
        rootstrap
        pbuilder

    written in python
        4000 LOC
        uses twisted web

    features
        importing of apt cache into archive using apt-proxy-import
        rsync for rsyncd backend
        cache cleaning of ununsed/old versions
        archive kept up to date via: ftp, http, rsync

    usage
        you configure apt to point to apt-proxy instead of the real archive
    

        configure global [DEFAULT] section
            address
            port
            min_refresh_delay       # how often to refresh Packages and other control files (default off)
            max_versions            # how many versions of a package to keep at maximum (off by default)
                
        for each resource (e.g., debian, backports) configure

            backends
                multiple backends supported for failover

    gotcha
        apt-proxy-import broken on Ubuntu
        does it import from apt-move repository?
            no it doesn't

    received bad reviews
    runs as user aptproxy
    
apt-cacher      caching proxy system for Debian package and source files
    drop-in replacement for apt-proxy
    perl program
        1700 LOC

    support utilities
        remove obsolete package files
        usage reports
        experimental features

    usage
        append proxy address to sources
            deb http://mirror.aarnet.edu.au/debian unstable main contrib non-free
                becomes

            deb http://proxy.example.com:3142/mirror.aarnet.edu.au/debian unstable main contrib non-free

        only supports http
            doesn't support ftp, rsync

        can be configured to run 
            standalone (recommended)
            as an inetd server
            CGI script (not recommended)

        interesting configuration options
            offline_mode        avoid outgoing connections completely
            expiry_hours        how many hours Package/Release files cached before assumed too old

        you can import debs
            putting them into import/ subdir of cache
            run /usr/share/apt-cacher/apt-cacher-import.pl

    pros
        offline mode

    cons
        doesn't decouple front-end APT configuration from backend configuration
        written in perl

    gotcha
        daemon_addr=localhost # doesn't work!
            daemon_addr=127.0.0.1
        
        edit /etc/default/apt-cacher
            AUTOSTART=1
            
                otherwise /etc/init.d/apt-cacher doesn't start

       
approx      caching proxy server for Debian archive files
    replacement for apt-proxy
    written in OCaml
        1641 LOC

    simplest program - tiny!
    least configurable / simplest configuration
        rewrites resources to targets

        e.g.,
          deb     http://apt:9999/debian    testing main
          deb     http://apt:9999/security  testing/updates main
          deb-src http://apt:9999/debian    unstable main

          repository     http://remote-host/initial/path

    defaults to port 9999

    runs as user approx (nice)

    cons 
        doesn't support importing

MISC

apt-move    maintain Debian packages as package pool
    move them into heirarchy and generate Packages

* IDEAS

configure files to never expire
configure automatic traffic redirection?
    unless you redirect traffic selectively
        privacy problems
        cache will fill up and kick off older objects


* REMINDER: configuration of squid.conf

http_port 127.0.0.1:3128

adjust refresh patterns with
    refresh_pattern regex min percent max

    options
        override-expire
        ignore-no-cache
        ignore-reload

* RESOURCE: http://www.debian-administration.org/articles/237
    question: how to setup a local debian mirror?

* RESOURCE: http://www.nabble.com/-taprobane--Caching:-apt-cacher-vs-apt-proxy-t935469.html
    bad reviews for apt-proxy
    apt-cacher claimed to be better 

* RESOURCE: https://help.ubuntu.com/community/AptProxy

* RESOURCE: http://apt-proxy.sourceforge.net/

    </t>
<t tx="zaril.20100911091317">SUMMARY
    to do chroot we need suid privileges
    how do we do this correctly?

RESOURCE: http://www.cs.berkeley.edu/~daw/papers/setuid-usenix02.pdf

</t>
<t tx="zaril.20100912044439">* SUMMARY:
    giving up on squid for now - Gentoo package is broken

* GOTCHA:
Sep 12 02:54:38 [(squid)] comm_select_init: epoll_create(): (38) Function not implemented_
Sep 12 02:54:38 [squid] Squid Parent: child process 22865 exited due to signal 6
Sep 12 02:54:41 [squid] Squid Parent: child process 22867 started
Sep 12 02:54:41 [(squid)] comm_select_init: epoll_create(): (38) Function not implemented_
Sep 12 02:54:41 [squid] Squid Parent: child process 22867 exited due to signal 6
Sep 12 02:54:44 [(squid)] comm_select_init: epoll_create(): (38) Function not implemented_
Sep 12 02:54:44 [squid] Squid Parent: child process 22869 started
Sep 12 02:54:44 [squid] Squid Parent: child process 22869 exited due to signal 6

    try using a different configuration?

* RESOURCE: http://gentoo-wiki.com/HOWTO_squid/squidGuard

recommended configuration
    http_port 3128					#squids listening port 3128 is default
    cache_mem 50 MB					#How much memory squid will use for caching 
    visible_hostname my-server			#Name of our server
    cache_dir ufs /var/cache/squid 500 16 256	#Directory where squid stores the cache, 
                            #500 means we use 500MB diskspace for caching
                            #16 and 256 sets how many directorys squid will use, this is default
    offline_mode off				#offline mode is really cool, if activated squid will always use the cache
                            #if the website is not in the cache, squid will fetch it.
                            #if you press reload in your browser, squid will fetch it again.
    maximum_object_size 102400 KB			#if a file is bigger then 102400 KB squid will not cache it.
    reload_into_ims off				#if activated squid will ignore reload requests from browsers, and use
                            #the cache if available
    pipeline_prefetch on				#squid will fetch data parallel
    
    acl my_network src 192.168.0.0/255.255.255.0	#Our network
    acl all src 0.0.0.0/0.0.0.0			#all networks
    
    http_access allow my_network			#allow access for our network
    http_access deny all				#and deny from all others
</t>
<t tx="zaril.20100912052439">debootstrap jaunty jaunty http://apt:9999/ubuntu
</t>
<t tx="zaril.20100912052909">emacs /etc/hosts
    127.0.0.1   apt

ping apt
    
emacs /etc/apt/sources.list
    sed 's/archive.ubuntu.com/apt:9999

apt-get update

import packages from apt-cache?
    no it doesn't work - broken on ubuntu


</t>
<t tx="zaril.20100912055420">maintains a local mirror from various sources

configured by default to create a mirror from apt's cache

caches the control file of packages
    .index/&lt;package&gt;

configuration file
    LOCALDIR        absolute path to your mirror
        e.g., LOCALDIR=/mirrors/ubuntu

    DIST
        e.g., DIST=stable

edit sources.list
    deb file:///mirrors/ubuntu stable main

    
apt-move get
    generates master files (used internally to determine what is available)

apt-move move
    moves files to local mirror location
        LOCALDIR=/mirrors/debian

apt-move packages
    generates the dists pointer (Packages)

GOTCHA:
    apt-move packages aren't authenticated
        http://wiki.debian.org/SecureApt</t>
<t tx="zaril.20100912065617">A2: debootstrap, which uses wget.  This means you can easily install new
    machine using the packages out of your apt-proxy cache.  In boot floppies,
    specify http://APTPROXY:9999/main as your debian mirror (replacing APTPROXY
    with the name or IP address of the machine where apt-proxy is running).

A3: rootstrap, a tool for making root images for user-mode-linux.  Assuming
    that you are running rootstrap on the same machine as apt-proxy and have
    used the default network addresses 192.168.10.x, put this in
    rootstrap.conf:

        mirror=http://192.168.10.1:9999/main

    [Note: during testing, we encountered a strange problem where rootstrap
    thought the architecture was i386-none, so we had to add --arch=i386 to the
    deboostrap call in /usr/lib/rootstrap/modules/debian.]

A4: pbuilder, which also uses debootstrap.  Add this to /etc/pbuilderrc:

        MIRRORSITE=http://APTPROXT:9999/main
        NONUSMIRRORSITE=http://APTPROXT:9999/non-US
</t>
<t tx="zaril.20100916032546">SUMMARY
    location of Packages/Sources
        /var/lib/apt/lists

build dependencies
    *-dev (of libraries)

some build dependencies conflict
    different packages depend on different conflicting versions
    some build dependencies may have `conflicts' headers that limit each other
        e.g., some mtas

Q: how much are build dependencies actually a problem?
    Q: how many build-dependencies? (in all of Debian)
        (download Sources)

Q: is it practical to just install all build dependencies?

Q: how many? how large?

INSIGHT: the lack of build dependencies is a QA feature
    catch missing build-depends

* analysis of build-dependencies in Ubuntu

cat /var/lib/apt/lists/*Sources | grep-dctrl -n -s Build-Depends  ""|sed 's/, /\n/g'|sort -u &gt; build-depends
    7238 different packages with different versions

cat build-depends | perl -pe 's/\s*[,\|]\s*/\n/g' | perl -pe 's/\s*\(.*//; s/^\s*//; s/\[.*//' | sort -u &gt; build-depends-pkgs
    3078 different packages (multiple versions counted)

apt-cache show $(cat build-depends-pkgs) | grep-dctrl -n -s Installed-Size "" | awk '{ sum += $1 } END { print sum }' 
    8GB worth of build-dependencies


IDEA: extract build dependencies for the packages in world

cat /turnkey/repository/*/*/Packages &gt; sphinx
apt-cache showsrc $(cat sphinx | grep-dctrl -n -s Package "" |sort -u) &gt; sphinx-sources
    567 binaries
    546 sources

cat sphinx-sources |grep-dctrl -n -s Build-Depends "" | perl -pe 's/\s*[,\|]\s*/\n/g' |sort -u &gt; sphinx-sources-builddeps 
    742 build depends (with different versions)

cat sphinx-sources-builddeps |  perl -pe 's/\s*\(.*//; s/^\s*//; s/\[.*//' |sort -u &gt; sphinx-sources-builddeps-pkgs
    438 build depends (different versions counted once)

apt-cache show $(cat sphinx-sources-builddeps-pkgs) | grep-dctrl -n -s Installed-Size "" | awk '{ sum += $1 } END { print sum }'
    771MB

</t>
<t tx="zaril.20100918092126">apt-build
debian-builder




</t>
<t tx="zaril.20100923043734">assume get_sources returns:
    /path/to/package: version

get_sources logic
    walk the tree
        any directory that has debian/ in it
            and is not under debian/

Q: how do we get the version?
parse output from dpkg-parsechangelog
    Version: ...
        
        calls /usr/lib/dpkg/parsechangelog/debian
            strips trailing whitespace
            skips newlines
        
                ^(\w[-+0-9a-z.]*) \(([^\(\) \t]+)\)((\s+[-+0-9a-z.]+)+)\;/i
parse the changelog ourselves
</t>
<t tx="zaril.20100923071058"></t>
</tnodes>
</leo_file>
