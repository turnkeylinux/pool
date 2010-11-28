class A(object):
    a = None
    def __init__(self, a):
        self.a = a
        self.b = 42
        
    def __setattr__(self, attrname, val):
        if hasattr(self.__class__, attrname):
            object.__setattr__(self, attrname, val)
            return
        
        print "__setattr__(%s, %s)" % (`attrname`, `val`)

a = A(111)
print a.a
print a.b


