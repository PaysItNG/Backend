from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView,DestroyAPIView
from rest_framework.response import Response
# Create your views here.
from rest_framework.decorators import api_view

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


@api_view(['GET'])
def APIendpoints(request):

    data = [
            [
            'auth/',
            ['register/', 'activate/account/', 'login/','verify/social/',
             'password/change/', 'password/verify/',
             'kyc/apply/', 'kyc/status/','kyc/approve/<str:id>/']
            ],

             ['virtual-card/',
              ['create/','retrieve/cardholder/','update/cardholder', 'fund/payment/',
               'ephemeral/keys/','payment/webhook/', "more/"],
             ],

           
             [ 'payment/',
              [
                 "paystack-webhook/", 'api/banks-list/','bank/transfer/',
                 'create-bank-accounts/', 'retrieve/user/account-list/',
                  
              ]
              
                 
             ],

             
              
             ]
    return Response(data)


