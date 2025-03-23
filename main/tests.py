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



# def get_common_subset(k):
#     new_arr=[]
#     for arr in range(0,len(k)):
#         # print(k[arr])
#         for val in k[0]:
           
#             if val in k[1] and k[2]:
#                 new_arr.append(val)
#     return list(set(new_arr))

# print(get_common_subset([[3,4,7,9], [2,3,4,6,7,8,11], [3,4,5,7,10]]))




from typing import List


# class Solution:
#     def merge(self,nums1: List[int], m: int, nums2: List[int], n: int) -> None:

#         """
#         Do not return anything, modify nums1 in-place instead.
#         """
#         nums1=nums1+nums2
#         arr=[]
#         for num in nums1:
#             if len(arr)<6 and num !=0:
#                 arr.append(num)
#         nums1=arr

        
#         # nums1=list(filter(lambda x: x != 0   ,nums1))
#         nums1.sort()
#         return nums1


# # nums = [1, 1, 2, 2, 3, 4, 4, 5]
# k=Solution()
# result=k.merge([1,2,3,0,0,0],3,[2,5,6],3)
# print(result)

class Solution:
    def reverseString(self, s: List[str]) -> None:
        i=len(s)-1
        arr=[]
        while i >=0:
            arr.append(s[i])
            i-=1
        
        
        print(arr)
            
        """
        Do not return anything, modify s in-place instead.
        """
s=Solution()
s.reverseString(["h","e","l","l","o"])
        


class Solution:
    def reverseString(self, s: List[str]) -> None:
        s.reverse()
        print(s)
            
        """
        Do not return anything, modify s in-place instead.
        """
s=Solution()
s.reverseString(["h","e","l","l","o"])
        