def appendTwice(c, b):
    d = [1]
    c.append(b)
    c.append(b)
    return 0

a = []
a.append(1)
b = appendTwice(a, 2)
print(a)