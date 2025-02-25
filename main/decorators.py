from rest_framework.response import Response
from django.shortcuts import render
from rest_framework import status

def SuperAdminAccess(view_func):
    def wrapper_func(self,*args,**kwargs):
        if self.request.user.role != 'admin1':
            return Response({
                'status':status.HTTP_403_FORBIDDEN,
                'message':'Can\'t perform this action'
            })
        else:

            return view_func(self,*args,**kwargs)
    return wrapper_func