#!/usr/bin/python
"""Prints source build log for package"""
import re
import sys
import pool
import help
import commands

def fatal(s):
    print >> sys.stderr, "error: " + str(s)
    sys.exit(1)

@help.usage(__doc__)
def usage():
    print >> sys.stderr, "Syntax: %s package[=version]" % sys.argv[0]

def extract_source_name(path):
    def extract_control(path):
        return commands.getoutput("ar -p %s control.tar.gz | zcat | tar -O -xf - control ./control 2>/dev/null" % path)

    def parse_control(contents):
        return dict([ re.split("\s*:\s+", line.strip(), 1)
                      for line in contents.split("\n")
                      if line.strip() and not line.startswith(" ") ])

    fields = parse_control(extract_control(path))
    if 'Source' in fields:
        return fields['Source']

    return None

def getpath_cached(p, package):
    """get path of cached package, whether in the pool or in a subpool"""
    path = p.pkgcache.getpath(package)
    if path:
        return path

    for subpool in p.subpools:
        path = getpath_cached(subpool, package)
        if path:
            return path

    return None
    
def main():
    args = sys.argv[1:]
    if not args:
        usage()

    package = args[0]

    try:
        p = pool.Pool()
    except pool.Error, e:
        fatal(e)
    
    source_package = package
    deb = getpath_cached(p, package)
    if deb:
        source_name = extract_source_name(deb)
        if source_name:
            source_package = source_name
            if '=' in package:
                source_package += "=" + package.split("=", 1)[1]

    path = p.getpath_build_log(source_package)
    if not path:
        fatal("no build log for `%s' (%s)" % (package, source_package))
        
    for line in file(path).readlines():
        print line,

if __name__ == "__main__":
    main()
