"""Transparent forking module

This module supports transparent forking by wrapping either:
A) a regular function (forked_func method): creates a subprocess for
every invocation of the function.

B) an instance constructor (forked_constructor): creates a subprocess
for every instance created, and proxies method calls to the instance
into the subprocess.

Return values from the wrapped function or wrapper instance methods
are serialized.  Exceptions are also serialized and reraised in the
parent process.

Example usage:

    def add(a, b):
        return a + b

    forkedadd = forked_func(add)
    print forkedadd(1, 1)

    class Adder:
        def add(self, a, b):
            return a + b
    ForkedAdder = forked_constructor(Adder)

    instance = ForkedAdder()
    print instance.add(1, 1)

    # pass an existing instance into a separate process
    class PidGetter:
        def getpid(self):
            return os.getpid()

    pg = PidGetter()
    
    def dummy():
        return pg
    forkedpg = forked_constructor(dummy)()
    print pg.getpid()
    print forkedpg.getpid()

    
"""

import os
import sys

import cPickle as pickle
import new

class Error(Exception):
    pass

def forked_func(func):
    def wrapper(*args, **kws):
        r_fd, w_fd = os.pipe()
        r_fh = os.fdopen(r_fd, "r", 0)
        w_fh = os.fdopen(w_fd, "w", 0)

        pid = os.fork()
        if pid == 0:
            # child
            r_fh.close()

            try:
                ret = func(*args, **kws)
            except Exception, e:
                pickle.dump(e, w_fh)
                sys.exit(1)

            pickle.dump(ret, w_fh)
            sys.exit(0)

        # parent
        w_fh.close()
        pid, status = os.waitpid(pid, 0)
        if not os.WIFEXITED(status):
            raise Error("child terminated unexpectedly")

        val = pickle.load(r_fh)
        error = os.WEXITSTATUS(status)
        if error:
            raise val
        return val
    return wrapper

class Pipe:
    def __init__(self):
        r, w = os.pipe()
        self.r = os.fdopen(r, "r", 0)
        self.w = os.fdopen(w, "w", 0)

class InstanceServer:
    def __init__(self, r, w, instance):
        self.r = r
        self.w = w
        self.instance = instance

    def run(self):
        while True:
            try:
                attrname, args, kws = pickle.load(self.r)
            except EOFError:
                break

            try:
                attr = getattr(self.instance, attrname)
                if not callable(attr):
                    raise Error("'%s' is not callable" % attrname)

                ret = attr(*args, **kws)
                pickle.dump((False, ret), self.w)
            except Exception, e:
                pickle.dump((True, e), self.w)

class InstanceClient:
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

def forked_constructor(constructor):
    """Wraps a constructor so that instances are created in a subprocess.
    Returns a new constructor"""
    def wrapper(*args, **kws):
        pid, r, w = forkpipe()
        if pid == 0:
            instance = constructor(*args, **kws)
            InstanceServer(r, w, instance).run()
            sys.exit(0)

        return InstanceClient(r, w)
    return wrapper

def test():
    def add(a, b):
        return a + b

    forkedadd = forked_func(add)
    print ">>> forkedadd(1, 1)"
    print forkedadd(1, 1)

    class Adder:
        def add(self, a, b):
            return a + b

    ForkedAdder = forked_constructor(Adder)

    print ">>> instance = ForkedAdder()"
    instance = ForkedAdder()

    print ">>> instance.add(1, 1)"
    print instance.add(1, 1)

    class PidGetter:
        def getpid(self):
            return os.getpid()

    pg = PidGetter()
    
    def dummy():
        return pg
    forkedpg = forked_constructor(dummy)()
    print pg.getpid()
    print forkedpg.getpid()


class Foo(object):
    def __init__(self, foo):
        self.foo = foo

    def getfoo(self):
        return self.foo

foo = forked_constructor(Foo)(666)
print foo.getfoo()
print foo.foo

