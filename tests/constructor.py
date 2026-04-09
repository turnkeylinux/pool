class B(object):
    def __init__(self, b):
        print("B.__init__")
        self.b = b

    def get(self):
        return 666
        
class A(B):
    def __new__(self, a):
        return a
        return B(a)
        print("__new__(%s)" % repr(a))
        a = object.__new__(self, a)
        print("foo")
        return a
    
#        return super(A, self).__new__(self, a) ## equivalent

    def __init__(self, a):
        print("__init__(%s)" % repr(a))
        self.a = a