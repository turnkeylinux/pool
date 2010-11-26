import os
import sys

import pickle

class Foo:
    def getuid(self):
        return os.getuid()

    def getpid(self):
        return os.getpid()


print "caller pid: %d" % os.getpid()
foo = Foo()
print foo.getuid()
print "foo pid: %d" % os.getpid()

    
