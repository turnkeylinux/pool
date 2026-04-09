class B:
    def __init__(self, b):
        self.b = b
        
class A(object):
    def __new__(cls, a):
        print("__new__(%s)" % repr(a))
        return object.__new__(cls)
#        return super(A, cls).__new__(cls) ## equivalent

    def __init__(self, a):
        print("__init__(%s)" % repr(a))
        self.a = a