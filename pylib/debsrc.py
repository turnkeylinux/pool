import re
from os.path import *

def cmp_versions(a, b):
    """Compare a with b according to Debian versioning criteria"""

    def normalize(v):
        return re.sub(r'(\D|\b)0+', r'\1', v).rstrip("-")
        
    return cmp(normalize(a), normalize(b))

def get_packages(srcpath):
    controlfile = join(srcpath, "debian/control")
    return [ re.sub(r'^.*?:', '', line).strip()
             for line in file(controlfile).readlines()
             if re.match(r'^Package:', line, re.I) ]

