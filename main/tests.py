# from django.test import TestCase
# import random

# Create your tests here.

char='0123456789'
val=''
for c in char:

    k=''
    if char.index(c) %4 ==0:
        k=f' {c}'
    else:
        k=c
    val+=k
    
    
print(val)