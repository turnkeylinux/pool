class B:
    def __init__(self, b):
        self.b = b
        
class A(object):
    def __new__(self, a):
        print "__new__(%s)" % `a`
        return object.__new__(self, a)
#        return super(A, self).__new__(self, a) ## equivalent

    def __init__(self, a):
        print "__init__(%s)" % `a`
        self.a = a
        
