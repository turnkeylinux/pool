import re

def normalize(v):
    return re.sub(r'(\D|\b)0+', r'\1', v)

def parse(v):
    if ':' in v:
        epoch, v = v.split(':', 1)
    else:
        epoch = 0

    if '-' in v:
        upstream_version, debian_revision = v.rsplit('-', 1)
    else:
        upstream_version = v
        debian_revision = ''

    return epoch, upstream_version, debian_revision
    
def compare(a, b):
    """Compare a with b according to Debian versioning criteria"""

    return cmp(parse(normalize(a)), parse(normalize(b)))
