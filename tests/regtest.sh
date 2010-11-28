#!/bin/sh

usage() {
    echo "syntax: $0 [ --options ]"
    echo 
    echo "  If no testing options are specified - test everything"
    echo
    echo "Options:"
    echo "  --notests   turn off tests"
    echo "  --nodelete  dont delete test pool at the end"
    echo "              (default if test fails)"
    echo 
    echo "  --info      test pool-info"
    echo "  --list      test pool-list"
    echo "  --exists    test pool-exists"
    echo "  --commit    test new version detection after committing to stocks"
    echo "  --getnew    test pool-get of newest versions"
    echo "  --getall    test pool-get of all versions (new and old)"
    echo "  --gc        test garbage collection"

    
    exit 1
}

if [ "$1" == "-h" ]; then
    usage
fi

for arg; do
    case "$arg" in
	--nodelete)
	    nodelete=yes
	    ;;

        --info)
	    test_info=yes
            ;;
        --list)
	    test_list=yes
            ;;
        --exists)
	    test_exists=yes
            ;;
        --commit)
	    test_commit=yes
            ;;
        --getnew)
	    test_getnew=yes
            ;;
        --getall)
	    test_getall=yes
            ;;
        --gc)
	    test_gc=yes
            ;;
	    
	--notests)
	    test_notests=yes
	    ;;
        *)
	    usage
    esac
done

OPTS="info list exists commit getnew getall gc notests"

noopts=yes
for opt in $OPTS; do
    if [ -n "$(eval echo \$test_$opt)" ]; then
	noopts=no
    fi
done

if [ "$noopts" = "yes" ]; then
    for opt in $OPTS; do
	eval test_$opt=yes
    done
fi

set -ex
base=$(pwd)

export TMPDIR=/turnkey/tmp/pool
mkdir -p $TMPDIR

testbase=$(mktemp -d -t test.XXXXXX)

cd $testbase
pool-init /turnkey/fab/buildroots/jaunty

mkdir subpool
tar -C subpool -xvf $base/regtest-stocks.tar.bz2 

cd subpool
pool-init /turnkey/fab/buildroots/jaunty
for stock in stocks/*; do
    pool-register $stock
    pool-unregister $stock
    pool-register $stock
done

cd ../
pool-register subpool

if [ -n "$test_info" ]; then
    pool-info -r
    pool-info -r --stocks
    pool-info -r --subpools

    pool-info -r --build-root
    pool-info -r --build-logs
    
    pool-info -r --pkgcache
    pool-info -r --stock-sources
    pool-info -r --stock-binaries
fi

if [ -n "$test_list" ]; then
    pool-list
    pool-list -a
    pool-list -n

    pool-list 'x*'
    pool-list -a '*'
fi

if [ -n "$test_exists" ]; then
    for pkg in $(pool-list -n); do
	pool-exists $pkg
    done

    for pkg in $(pool-list -a); do
	pool-exists $pkg
    done

    pool-exists nosuchpackage || true
    pool-exists nosuchpackage=1.1 || true
fi

if [ -n "$test_commit" ]; then
    echo === testing committing to stocks
    pool-list 

    # save previous versions in environment variables
    for pkg in plain git1 git2 gitsingle; do
	eval $pkg=$(pool-list $pkg)
    done

    cd subpool/stocks/
    files="debian/changelog pylib/cmd_pyhello.py"
    cd plain/plain
    sed -i 's/1\.0/1.1/' $files
    cd ../../

    cd gitsingle
    echo '# foo' >> Makefile
    git-commit -v -m "increment autoversion" Makefile
    cd ../

    cd git
    cd git1
    sed -i 's/1\.1/1.2/' $files
    git-commit -v -m "increment to version 1.2" $files

    cd ../git2
    sed -i 's/1\.2/1.3/' $files
    git-commit -v -m "increment to version 1.3" $files
    cd ../../

    cd ../../../
    pool-list

    # if any of the versions haven't changed, raise the alarm
    for pkg in plain git1 git2 gitsingle; do
	[ "$(pool-list $pkg)" != "$(eval echo \$$pkg)" ] || false
    done
fi

if [ -n "$test_getall" ] || [ -n "$test_getnew" ]; then
    echo "=== getting all packages (building from source)"
    pool-get .
    rm *.deb

    echo "=== getting all packages (cached)"
    pool-get .
    rm *.deb

    echo "=== getting all packages into tree (cached)"
    mkdir tree
    pool-get -t tree
    find tree/

    echo "=== get newest packages by name"
    for pkg in $(pool-list -n); do
	pool-get . $pkg
    done

    rm *.deb
    pool-info -r --pkgcache
    pool-info -r --build-logs
fi

if [ -n "$test_getall" ]; then
    echo "=== get historical versions of packages"
    for pkg in $(pool-list -a); do
	pool-get . $pkg
    done

    pool-info -r --pkgcache
    pool-info -r --build-logs
fi

if [ -z "$nodelete" ]; then
    echo === destroying test pool $testbase

    cd subpool
    for stock in $(pool-info --stocks; pool-info --subpools); do
	pool-unregister $stock
    done
    cd ../
    pool-unregister subpool
    rm -rf subpool
    rm -rf $testbase
else
    echo
    echo PRESERVING TEST POOL: $testbase
fi







