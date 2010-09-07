<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet ekr_test?>
<leo_file>
<leo_header file_format="2" tnodes="0" max_tnode_index="0" clone_windows="0"/>
<globals body_outline_ratio="0.542443064182">
	<global_window_position top="0" left="507" height="966" width="758"/>
	<global_log_window_position top="0" left="0" height="0" width="0"/>
</globals>
<preferences/>
<find_panel_settings/>
<vnodes>
<v t="loni.20100827184947" a="E"><vh>Project</vh>
<v t="loni.20100827184947.1" a="E"><vh>design</vh>
<v t="loni.20100827184947.2" a="ETV"><vh>brainstorming</vh>
<v t="zaril.20100828060043"><vh>first draft</vh></v>
</v>
<v t="zaril.20100828055849"><vh>terminology</vh></v>
<v t="loni.20100827184947.4" a="E"><vh>file/data structure</vh></v>
<v t="loni.20100827184947.5" a="E"><vh>cli syntax</vh></v>
<v t="loni.20100827184947.6"><vh>usage examples</vh></v>
</v>
<v t="loni.20100827184947.7" a="E"><vh>implementation</vh>
<v t="zaril.20100906050211" a="E"><vh>implement full command set for binaries in regular directories</vh>
<v t="zaril.20100906050211.1"><vh>init /path/to/build-chroot</vh></v>
<v t="zaril.20100906050211.2"><vh>register / unregister # regular directories</vh></v>
<v t="zaril.20100906230204"><vh>info</vh></v>
<v t="zaril.20100906050211.4"><vh>exists</vh>
<v t="zaril.20100907030232"><vh>refactor away stock</vh></v>
</v>
<v t="zaril.20100906050211.5"><vh>list</vh></v>
<v t="zaril.20100906050211.6"><vh>get</vh></v>
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
support regular sources in regular directories
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
<t tx="zaril.20100906050211.6"></t>
<t tx="zaril.20100906230204">* logic
    list .pool/stock subdirectories
    for each stock:
        print its path
</t>
<t tx="zaril.20100907030232">class PoolStocks:
    def __init__(self):
        pass

</t>
</tnodes>
</leo_file>
