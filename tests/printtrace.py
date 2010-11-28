import sys
import traceback
import pickle

class Error(Exception):
    pass

def foo():
    return bar()

def bar():
    raise Error("yo yo yo")

def main():
    foo()

if __name__=="__main__":
    try:
        main()
    except Exception, e:
        traceback.print_exc(file=sys.stderr)
        
#        raise e.__class__, e, sys.exc_traceback



        
        
        
