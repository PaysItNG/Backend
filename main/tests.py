# # from django.test import TestCase
# # import random

# # Create your tests here.

# char='012345345678911'
# val=''
# for index,c in enumerate(char):
 

#     k=''
#     if index %4 ==0:
#         k=f' {c}'
#     else:
#         k=c
#     val+=k
    
    
# print(val)
# first_4=''
# last_4=''

# for index,val in enumerate(char):
#     if char.index(val)==4:
#         first_4+=char[-4:]
#     # if char.index(val)==-4:
#     #     last_4+=char[-4]

# print(first_4)



def get_common_subset(k):
    new_arr=[]
    for arr in range(0,len(k)):
        # print(k[arr])
        for val in k[0]:
           
            if val in k[1] and k[2]:
                new_arr.append(val)
    return list(set(new_arr))

print(get_common_subset([[3,4,7,9], [2,3,4,6,7,8,11], [3,4,5,7,10]]))