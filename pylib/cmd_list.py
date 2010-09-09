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
import pool

from fnmatch import fnmatch

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [ <package-glob> ... ]" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)


def filter_packages(packages, globs):
    filtered = []
    for glob in globs:
        matches = [ (name, version) for name, version in packages
                    if fnmatch(name, glob) ]

        if not matches:
            print >> sys.stderr, "warning: %s: no matching packages" % glob
        else:
            filtered += matches

    return filtered
    
def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'an',
                                   ['all-versions', 'name-only'])
    except getopt.GetoptError, e:
        usage(e)

    all_versions = False
    name_only = False
    
    for opt, val in opts:
        if opt in ('-a', '--all-versions'):
            all_versions = True
        elif opt in ('-n', '--name-only'):
            name_only = True

    if name_only and all_versions:
        fatal("--name-only and --all-versions are conflicting options")
            
    packages = pool.Pool().list(all_versions)
    globs = args

    if globs:
        packages = filter_packages(packages, globs)
        
    if name_only:
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
