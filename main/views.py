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
from rest_framework import status

class UserProfileDataView(APIView):
    serializer_class=UserProfileSerializer
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def get(self,request,*args,**kwargs):
        try:
            profile=UserProfile.objects.get(user=request.user)
            serializer=self.serializer_class(profile).data

            serializer['user']=UserSerializer(User.objects.get(id=serializer['user']),many=False).data

            return Response({
                'data':serializer
            },status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'message':e,
                'data':{},

            },status=status.HTTP_404_NOT_FOUND)

    def put(self,request,*args,**kwargs):

        try:
            profile=UserProfile.objects.get(user=request.user)

            serializer=self.serializer_class(profile,data=request.data)

            if serializer.is_valid():
                serialized_data=serializer.save()

                return Response({
                    'message':'Profile successfully updated',
                    'data':self.serializer_class(serialized_data).data
                },status=status.HTTP_200_OK)
            
            else:

                return Response({
                    'message':'Invalid data',
                    'data':{}
                },status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
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
               'ephemeral/keys/','payment/webhook/', 'add/fund/','webhook/',"more/",'authorization/webhook/'],
             ],

           
             [ 'payment/',
              [
                 "paystack-webhook/", 'api/banks-list/','bank/transfer/',
                 'create-bank-accounts/', 'retrieve/user/account-list/',
                  
              ]
              
                 
             ],
             ['profile/'],
             ['vtu/',
              [
                  'validate/phone-number/','service/variations/','pay/airtime-data/',
                  'verify/meter/','pay/utility/',
              ]
              ]

             
              
             ]
    return Response(data)


