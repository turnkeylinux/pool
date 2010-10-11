import re

def normalize(v):
    return re.sub(r'(\D|\b)0+', r'\1', v)

def parse(v):
    if ':' in v:
        epoch, v = v.split(':', 1)
    else:
        epoch = ''

    if '-' in v:
        upstream_version, debian_revision = v.rsplit('-', 1)
    else:
        upstream_version = v
        debian_revision = ''

    return epoch, upstream_version, debian_revision

class VersionParser:
    def __init__(self, str):
        self.str = str

    def getlex(self):
        lex = re.match(r'(\D*)', self.str).group(1)
        self.str = self.str[len(lex):]
        
        return lex

    def getnum(self):
        num = re.match(r'(\d*)', self.str).group(1)
        self.str = self.str[len(num):]

        if num:
            return int(num)

        return 0
        
def _compare(s1, s2):
    if s1 == s2:
        return 0

    p1 = VersionParser(s1)
    p2 = VersionParser(s2)

    while True:
        l1 = p1.getlex()
        l2 = p2.getlex()

        val = cmp(l1, l2)
        if val != 0:
            return val

        n1 = p1.getnum()
        n2 = p2.getnum()
        val = cmp(n1, n2)
        if val != 0:
            return val

def compare(a, b):
    """Compare a with b according to Debian versioning criteria"""

    a = parse(normalize(a))
    b = parse(normalize(b))

    for i in range(3):
        val = _compare(a[i], b[i])
        if val != 0:
            return val

    return 0

def test():
    import time
    howmany = 1000
    start = time.time()
    for i in xrange(howmany):
        compare("0-2010.10.1-d6cbb928", "0-2010.10.10-a9ee521c")
    end = time.time()
    elapsed = end - start

    print "%d runs in %.4f seconds (%.2f per/sec)" % (howmany, elapsed,
                                                      howmany / elapsed)

if __name__ == "__main__":
    test()
