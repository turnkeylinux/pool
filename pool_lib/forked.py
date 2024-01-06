# Copyright (c) 2008 Liraz Siri <liraz@turnkeylinux.org>
#
# This file is part of turnkey-pylib.
#
# turnkey-pylib is open source software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.

"""Transparent forking module

This module supports transparent forking by wrapping either:
A) a regular function (forked_func method): the wrapper creates a subprocess
for every invocation of the function.

B) a constructor (forked_constructor): the wrapper creates a
subprocess for every instance created, and proxies method calls and
attribute setting and getting into the instance inside the subprocess.

Return values from the wrapped function or wrapper instance methods
are serialized.  Exceptions are also serialized and reraised in the
parent process.

Limitation: Forked functions or instance methods can not return any
value that can not be serialized with pickle. This includes:
        file objects
        tracebacks
        generators (I.e., created when you use yield)
        nested classes
        instance methods

Example usage:

    def add(a, b):
        return a + b

    forkedadd = forked_func(add)
    assert forkedadd(1, 1) == 2

    class Adder:
        def add(self, a, b):
            return a + b
    ForkedAdder = forked_constructor(Adder)

    instance = ForkedAdder()
    assert instance.add(1, 1) == 2

    # pass an existing instance into a separate process
    class PidGetter:
        def getpid(self):
            return os.getpid()

    pg = PidGetter()

    def dummy():
        return pg
    forkedpg = forked_constructor(dummy)()
    assert pg.getpid() != forkedpg.getpid()

    class Attr(object):
        def __init__(self, attr):
            self.attr = attr

        def getattr(self):
            return self.attr

        def setattr(self, attr):
            self.attr = attr

    attr = forked_constructor(Attr)(666)
    assert attr.attr == 666

    attr.setattr(111)
    assert attr.attr == 111

    attr.attr = 222
    assert attr.getattr() == 222

"""

import os
import sys

import traceback
import pickle as pickle
import types
from typing import Callable, Any, Tuple, BinaryIO, no_type_check


class Error(Exception):
    pass


def forked_func(func: Callable[..., Any],
                print_traceback: bool = False
                ) -> Callable[..., Any]:
    def wrapper(*args: Any, **kws: Any) -> Any:
        r_fd, w_fd = os.pipe()
        rb_fh = os.fdopen(r_fd, "rb", 0)
        wb_fh = os.fdopen(w_fd, "wb", 0)

        pid = os.fork()
        if pid == 0:
            # child
            rb_fh.close()

            try:
                ret = func(*args, **kws)
            except Exception as e:
                if print_traceback:
                    traceback.print_exc(file=sys.stderr)
                pickle.dump(e, wb_fh)
                os._exit(1)

            pickle.dump(ret, wb_fh)
            os._exit(0)

        # parent
        wb_fh.close()
        pid, status = os.waitpid(pid, 0)
        if not os.WIFEXITED(status):
            raise Error("child terminated unexpectedly")

        val = pickle.load(rb_fh)
        error = os.WEXITSTATUS(status)
        if error:
            raise val
        return val

    return wrapper


class Pipe:
    def __init__(self) -> None:
        r, w = os.pipe()
        self.r: BinaryIO = os.fdopen(r, "rb", 0)
        self.w: BinaryIO = os.fdopen(w, "wb", 0)


class ObjProxyBase:
    OP_CALL = "call"
    OP_GET = "get"
    OP_SET = "set"
    ATTR_CALLABLE = "__attr_callable__"


class ObjProxyServer(ObjProxyBase):
    def __init__(
            self, r: BinaryIO, w: BinaryIO,
            obj: Any, print_traceback: bool = False):
        self.r = r
        self.w = w
        self.obj = obj
        self.print_traceback = print_traceback

    def run(self) -> None:
        while True:
            try:
                op, params = pickle.load(self.r)
            except (EOFError, KeyboardInterrupt):
                break

            if op == self.OP_CALL:
                op_handler = self._handle_op_call
            elif op == self.OP_GET:
                op_handler = self._handle_op_get
            elif op == self.OP_SET:
                op_handler = self._handle_op_set
            else:
                raise Error(f"illegal ObjProxy operation ({op})")

            op_handler(params)

    @staticmethod
    def _write_result(method: Callable[..., None]) -> Callable[..., None]:
        @no_type_check
        def wrapper(self, *args: Any, **kws: Any) -> Any:
            try:
                ret = method(self, *args, **kws)
                pickle.dump((False, ret), self.w)
            except Exception as e:
                if self.print_traceback:
                    if not isinstance(e, AttributeError):
                        traceback.print_exc(file=sys.stderr)
                pickle.dump((True, e), self.w)

        return wrapper

    @_write_result.__func__
    def _handle_op_call(self, params: Tuple[str, list, dict]) -> Any:
        attrname, args, kws = params
        attr = getattr(self.obj, attrname)
        if not callable(attr):
            raise Error("'%s' is not callable" % attrname)
        return attr(*args, **kws)

    @_write_result.__func__
    def _handle_op_get(self, params: Tuple[str]) -> Any:
        attrname, = params
        val = getattr(self.obj, attrname)
        if callable(val):
            return self.ATTR_CALLABLE
        return val

    @_write_result.__func__
    def _handle_op_set(self, params: Tuple[str, list]) -> Any:
        attrname, val = params
        setattr(self.obj, attrname, val)


def _read_result(op_method: Callable[..., None]) -> Callable[..., Any]:
    def wrapper(self, *args, **kws):
        op_method(self, *args, **kws)
        error, val = pickle.load(self._r)
        if error:
            raise val
        return val

    return wrapper


class ObjProxyClient(ObjProxyBase):
    """Object proxy client.

    Transparently handles:
    * method invocations
    * attribute setting
    * attribute getting

    """

    __local_attr__ = ["_r", "_w"]

    def __init__(self, r: BinaryIO, w: BinaryIO):
        self._r = r
        self._w = w

    @_read_result
    def _op_call(self, attrname: str, args: list, kws: dict) -> None:
        pickle.dump((self.OP_CALL, (attrname, args, kws)), self._w)

    @_read_result
    def _op_get(self, attrname: str) -> None:
        pickle.dump((self.OP_GET, (attrname,)), self._w)

    @_read_result
    def _op_set(self, attrname: str, val: Any) -> None:
        pickle.dump((self.OP_SET, (attrname, val)), self._w)

    def __setattr__(self, attrname: str, val: Any) -> None:
        if attrname in self.__local_attr__:
            return object.__setattr__(self, attrname, val)

        return self._op_set(attrname, val)

    def __getattr__(self, attrname: str) -> Any:
        val = self._op_get(attrname)
        if val != self.ATTR_CALLABLE:
            return val

        @no_type_check
        def unbound_method(self, *args, **kws):
            return self._op_call(attrname, args, kws)

        method = types.MethodType(unbound_method, self)
        object.__setattr__(self, attrname, method)
        return method


def forkpipe() -> Tuple[int, BinaryIO, BinaryIO]:
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


def forked_constructor(constructor: Callable[..., Any],
                       print_traceback: bool = False
                       ) -> Callable[..., ObjProxyClient]:
    """Wraps a constructor so that instances are created in a subprocess.
    Returns a new constructor"""

    @no_type_check
    def wrapper(*args, **kws):
        pid, r, w = forkpipe()
        if pid == 0:
            obj = constructor(*args, **kws)
            ObjProxyServer(r, w, obj, print_traceback=print_traceback).run()
            os._exit(0)

        return ObjProxyClient(r, w)

    return wrapper


def test():
    def add(a, b):
        return a + b

    forkedadd = forked_func(add)
    print(">>> forkedadd(1, 1)")
    print(forkedadd(1, 1))

    class Adder:
        def add(self, a, b):
            return a + b

    ForkedAdder = forked_constructor(Adder)

    print(">>> instance = ForkedAdder()")
    instance = ForkedAdder()

    print(">>> instance.add(1, 1)")
    print(instance.add(1, 1))

    class PidGetter:
        def getpid(self):
            return os.getpid()

    pg = PidGetter()

    def dummy():
        return pg

    forkedpg = forked_constructor(dummy)()
    print("pg.getpid() = %d" % pg.getpid())
    print("forkedpg.getpid() = %d" % forkedpg.getpid())
    assert pg.getpid() != forkedpg.getpid()

    class Attr(object):
        def __init__(self, attr):
            self.attr = attr

        def getattr(self):
            return self.attr

        def setattr(self, attr):
            self.attr = attr

    attr = forked_constructor(Attr)(666)
    print(">>> attr.attr")
    print(attr.attr)

    attr.setattr(111)
    assert attr.attr == 111

    print(">>> attr.attr = 222")
    attr.attr = 222
    print(">>> attr.getattr()")
    print(attr.getattr())
    assert attr.getattr() == 222


if __name__ == "__main__":
    test()
