import os
import sys

import pickle

class _Foo:
    def getuid(self):
        return os.getuid()

    def getpid(self):
        return os.getpid()

class Error(Exception):
    pass

class Pipe:
    def __init__(self):
        r, w = os.pipe()
        self.r = os.fdopen(r, "r", 0)
        self.w = os.fdopen(w, "w", 0)

class FooProxy:
    def __init__(self, r, w):
        self.r = r
        self.w = w

    def getpid(self):
        pickle.dump(('getpid', ()), self.w)
        error, val = pickle.load(self.r)
        if error:
            raise val
        return val

def forkpipe():
    """Forks and create a bi-directional pipe -> (pid, r, w)"""
    pipe_input = Pipe()
    pipe_output = Pipe()
    
    pid = os.fork()
    if pid == 0:
        pipe_output.r.close()
        pipe_input.w.close()

        return (pid, pipe_input.r, pipe_output.w)
    else:
        pipe_output.w.close()
        pipe_input.r.close()
        
        return (pid, pipe_output.r, pipe_input.w)

def Foo():
    pid, r, w = forkpipe()
    if pid == 0:
        obj = _Foo()
        while True:
            try:
                attrname, args = pickle.load(r)
            except EOFError:
                break

            attr = getattr(obj, attrname)
            if not callable(attr):
                raise Error("'%s' is not callable" % attrname)

            try:
                ret = attr(*args)
                pickle.dump((False, ret), w)
            except Exception, e:
                pickle.dump((True, e), w)

        sys.exit(0)

    return FooProxy(r, w)
                    
        
print "caller pid: %d" % os.getpid()
foo = Foo()
print "foo pid: %d" % foo.getpid()

    
