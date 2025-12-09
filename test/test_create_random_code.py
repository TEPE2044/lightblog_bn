import random
# code is the kind of str by using join and random.choices
code = ''.join(random.choices('0123456789', k=4))
print(code, type(code))

