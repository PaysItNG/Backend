# from django.test import TestCase

# Create your tests here.
open_brace='('
closed_brace=')'
brace=')()())'
out=''
for i,val in enumerate(brace):
    if val == '(' and brace[i+1]==')':
        out+=val+brace[i+1]
print(str(out))

