import os
import sys

import pickle

class FooError(Exception):
    pass

class _Foo:
    def getuid(self):
        return os.getuid()

    def getpid(self):
        return os.getpid()

    def add(self, a, b):
        return a + b

    def makedict(self, name, age):
        return {'name': name, 'age': 26}

class Error(Exception):
    pass

class Pipe:
    def __init__(self):
        r, w = os.pipe()
        self.r = os.fdopen(r, "r", 0)
        self.w = os.fdopen(w, "w", 0)

import new
class ProxyInstance:
    """This proxy class only proxies method invocations - no attributes"""
    def __init__(self, r, w):
        self.r = r
        self.w = w

    @staticmethod
    def _proxy(attrname):
        def method(self, *args, **kws):
            pickle.dump((attrname, args, kws), self.w)
            error, val = pickle.load(self.r)
            if error:
                raise val
            return val
        return method

    def __getattr__(self, name):
        print "GETATTR"
        unbound_method = self._proxy(name)
        method = new.instancemethod(unbound_method,
                                    self, self.__class__)
        setattr(self, name, method)
        return method

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
                attrname, args, kws = pickle.load(r)
            except EOFError:
                break

            try:
                attr = getattr(obj, attrname)
                if not callable(attr):
                    raise Error("'%s' is not callable" % attrname)

                ret = attr(*args, **kws)
                pickle.dump((False, ret), w)
            except Exception, e:
                pickle.dump((True, e), w)

        sys.exit(0)

    return ProxyInstance(r, w)
        
print "caller pid: %d" % os.getpid()
foo = Foo()
print "1 + 1 = %d" % foo.add(1, 1)
print "dict: " + `foo.makedict("liraz", age=26)`

print "foo pid: %d" % foo.getpid()
print "foo pid: %d" % foo.getpid()
print "foo uid: %d" % foo.getuid()

    
