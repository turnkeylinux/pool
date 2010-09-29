import re
import os
from os.path import *

class Error(Exception):
    pass

def cmp_versions(a, b):
    """Compare a with b according to Debian versioning criteria"""

    def normalize(v):
        return re.sub(r'(\D|\b)0+', r'\1', v).rstrip("-")
        
    return cmp(normalize(a), normalize(b))

def get_paths(path):
    if isfile(join(path, "debian", "control")):
        return [ path ]

    paths = []
    for subname in os.listdir(path):
        subpath = join(path, subname)
        if isdir(subpath):
            paths.extend(get_paths(subpath))
    return paths

def get_version(srcpath):
    changelogfile = join(srcpath, "debian/changelog")
    if not exists(changelogfile):
        raise Error("no such file or directory `%s'" % changelogfile)
    
    for line in file(changelogfile).readlines():
        m = re.match('^\w[-+0-9a-z.]* \(([^\(\) \t]+)\)(?:\s+[-+0-9a-z.]+)+\;',line, re.I)
        if m:
            return m.group(1)

    raise Error("can't parse version from `%s'" % changelogfile)

def get_packages(srcpath):
    controlfile = join(srcpath, "debian/control")
    return [ re.sub(r'^.*?:', '', line).strip()
             for line in file(controlfile).readlines()
             if re.match(r'^Package:', line, re.I) ]


