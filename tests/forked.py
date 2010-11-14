import os
import sys

import pickle

class Error(Exception):
    pass

def forked(method):
    def wrapper(*args, **kws):
        r_fd, w_fd = os.pipe()
        r_fh = os.fdopen(r_fd, "r", 0)
        w_fh = os.fdopen(w_fd, "w", 0)

        pid = os.fork()
        if pid == 0:
            # child
            r_fh.close()

            try:
                ret = method(*args, **kws)
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
    
@forked
def test(s):
    print "test pid: " + `os.getpid()`
    # raise Error("foo")
    return "test: " + str(s)

print "parent pid: " + `os.getpid()`
try:
    print `test("string")`
except Error, e:
    print "caught Error: " + str(e)

    
