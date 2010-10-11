import re
import string

def parse(v):
    if ':' in v:
        epoch, v = v.split(':', 1)
    else:
        epoch = '0'

    if '-' in v:
        upstream_version, debian_revision = v.rsplit('-', 1)
    else:
        upstream_version = v
        debian_revision = '0'

    return epoch, upstream_version, debian_revision

class VersionParser:
    def __init__(self, str):
        self.str = str

    def getlex(self):
        str = self.str
        i = 0
        for c in str:
            if c in '0123456789':
                break
            i += 1

        if i:
            lex = str[:i]
            self.str = str[i:]

            return lex

        return ''

    def getnum(self):
        str = self.str
        i = 0
        for c in str:
            if c not in '0123456789':
                break
            i += 1

        if i:
            num = int(str[:i])
            self.str = str[i:]

            return num

        return 0
        
# _compare is functionally equivalent to _compare_flat
# only its much more readable
def _compare(s1, s2):
    if s1 == s2:
        return 0

    p1 = VersionParser(s1)
    p2 = VersionParser(s2)

    while True:
        n1 = p1.getnum()
        n2 = p2.getnum()
        
        val = cmp(n1, n2)
        if val != 0:
            return val

        l1 = p1.getlex()
        l2 = p2.getlex()

        val = cmp(l1, l2)
        if val != 0:
            return val

        if p1.str == p2.str:
            return 0

# _compare_flat is functionally equivalent to _compare
# but it embeds VersionParser's functionality inline for optimization
def _compare_flat(s1, s2):
    if s1 == s2:
        return 0

    while True:
        # parse numeric component for comparison
        i = 0
        for c in s1:
            if c not in '0123456789':
                break
            i += 1

        if i:
            n1 = int(s1[:i])
            s1 = s1[i:]

        else:
            n1 = 0

        i = 0
        for c in s2:
            if c not in '0123456789':
                break
            i += 1

        if i:
            n2 = int(s2[:i])
            s2 = s2[i:]

        else:
            n2 = 0

        val = cmp(n1, n2)
        if val != 0:
            return val

        # if numeric components equal, parse lexical components
        i = 0
        for c in s1:
            if c in '0123456789':
                break
            i += 1

        if i:
            l1 = s1[:i]
            s1 = s1[i:]
        else:
            l1 = ''

        i = 0
        for c in s2:
            if c in '0123456789':
                break
            i += 1

        if i:
            l2 = s2[:i]
            s2 = s2[i:]
        else:
            l2 = ''

        val = cmp(l1, l2)
        if val != 0:
            return val

        if s1 == s2:
            return 0

def compare(a, b):
    """Compare a with b according to Debian versioning criteria"""

    a = parse(a)
    b = parse(b)

    for i in (0, 1, 2):
        val = _compare_flat(a[i], b[i])
        if val != 0:
            return val

    return 0

def test():
    try:
       import psyco; psyco.full()
    except ImportError:
       pass
    
    import time
    howmany = 10000
    start = time.time()
    for i in xrange(howmany):
        compare("0-2010.10.1-d6cbb928", "0-2010.10.10-a9ee521c")
    end = time.time()
    elapsed = end - start

    print "%d runs in %.4f seconds (%.2f per/sec)" % (howmany, elapsed,
                                                      howmany / elapsed)

if __name__ == "__main__":
    test()
