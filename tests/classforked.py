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


def Foo():
    pipe_input = Pipe()
    pipe_output = Pipe()
    
    pid = os.fork()
    if pid == 0:
        pipe_output.r.close()
        pipe_input.w.close()

        obj = _Foo()
        while True:
            try:
                attrname, args = pickle.load(pipe_input.r)
            except EOFError:
                break

            attr = getattr(obj, attrname)
            if not callable(attr):
                raise Error("'%s' is not callable" % attrname)

            try:
                ret = attr(*args)
                pickle.dump((False, ret), pipe_output.w)
            except Exception, e:
                pickle.dump((True, e), pipe_output.w)

        sys.exit(0)

    pipe_output.w.close()
    pipe_input.r.close()
    return FooProxy(pipe_output.r,
                    pipe_input.w)
                    
        
print "caller pid: %d" % os.getpid()
foo = Foo()
print "foo pid: %d" % foo.getpid()

    
