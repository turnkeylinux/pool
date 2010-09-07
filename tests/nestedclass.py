class A:
    def __init__(self, var):
        self.var = var

        class B:
            def foo(s):
                print s
                print self
                print self.var

        self.B = B

a = A(666)
b = a.B()
b.foo()
                


