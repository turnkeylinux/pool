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

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s [ <package-glob> ... ]" % sys.argv[0]

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

def main():
    try:
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'an',
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

    packages = Pool().list(opt_all_versions, *globs)
    for glob in packages.missing:
        print >> sys.stderr, "warning: %s: no matching packages" % glob
        
    for package in packages:
        if opt_name_only:
            print Pool.parse_package_id(package)[0]
        else:
            print package
        
if __name__=="__main__":
    main()
