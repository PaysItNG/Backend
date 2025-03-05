from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView,DestroyAPIView
from rest_framework.response import Response
# Create your views here.
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny
from userauth.views import getUserData
from .serializers import *

class UserProfileDataView(APIView):
    serializer_class=[UserProfileSerializer]
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def get(self,request,*args,**kwargs):
        pass




class DepositFundsView(APIView):
    pass