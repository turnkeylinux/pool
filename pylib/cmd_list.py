#!/usr/bin/python
"""List packages in pool

Options:
    -a --all-versions	print all available versions of a package in the pool
			(default: print the newest versions only)
    -n --name-only	print only the names of packages in the pool

"""
import sys
import help
import getopt
from pool import Pool

from fnmatch import fnmatch

import debversion

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [ <package-glob> ... ]" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)


def filter_packages(packages, globs):
    filtered = []
    for glob in globs:
        matches = []
        for package in packages:
            name, version = Pool.parse_package_id(package)
            if fnmatch(name, glob):
                matches.append(package)

        if not matches:
            print >> sys.stderr, "warning: %s: no matching packages" % glob
        else:
            filtered += matches

    return filtered
    
def list_packages(all_versions, globs=None):
    packages = Pool().list(all_versions)
    if globs:
        packages = filter_packages(packages, globs)

    return [ Pool.parse_package_id(package) for package in packages ]

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'an',
                                   ['all-versions', 'name-only'])
    except getopt.GetoptError, e:
        usage(e)

    opt_all_versions = False
    opt_name_only = False
    
    for opt, val in opts:
        if opt in ('-a', '--all-versions'):
            opt_all_versions = True
        elif opt in ('-n', '--name-only'):
            opt_name_only = True

    if opt_name_only and opt_all_versions:
        fatal("--name-only and --all-versions are conflicting options")

    globs = args
    packages = list_packages(opt_all_versions, globs)

    def _cmp(a, b):
        val = cmp(b[0], a[0])
        if val != 0:
            return val
        return debversion.compare(a[1], b[1])
        
    packages.sort(cmp=_cmp, reverse=True)

    if opt_name_only:
        names = set()
        for name, version in packages:
            names.add(name)

        for name in names:
            print name
    else:
        for name, version in packages:
            print "%s=%s" % (name, version)
        
if __name__=="__main__":
    main()
