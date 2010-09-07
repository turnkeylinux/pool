class A:
    def __init__(self, *arr):
        self.arr = list(arr)

    def __getitem__(self, key):
        return self.arr[key]

    def __setitem__(self, key, val):
        self.arr[key] = val

    def __iter__(self):
        return iter(self.arr)
    
