def func(var, arr=[]):
    arr.append(var)

    return arr

print(repr(func(1)))
print(repr(func(2)))