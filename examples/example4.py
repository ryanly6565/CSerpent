z = True
a = [1, 3, 69, z, [5, 50, 500]]
print(a)
a.remove(69)
a.remove(z)
a.pop(0)
a.append(200)
should_be_three = 0
should_be_three = len(a)
print(should_be_three)
print(a)
print([1, 2, 3])

lst2 = [1, 2]
should_be_two = lst2.pop(1)
print(should_be_two)