from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView,ListCreateAPIView
from .serializers import *
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import (AllowAny,
                                        IsAuthenticated,
                                        
                                        IsAuthenticatedOrReadOnly,
                                        IsAdminUser)
from rest_framework.response import Response
from rest_framework import generics,viewsets,status
from django.core.exceptions import ObjectDoesNotExist
from .models import *
from django.contrib.auth.hashers import check_password

# Create your views here.


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }



class SignupView(APIView):
    serializer_class=UserSerializer
    # authentication_classes=(JWTAuthentication,)
    permission_classes = (AllowAny,)

    def post(self,request):
        email=request.data.get('email')
        try:
            # print(User.objects.get(email=str(request.data.get('email'))))
            user=User.objects.get(email=email)
            print(type(user))
            serializer=UserSerializer(user)

            return Response({
                'status':status.HTTP_200_OK,
                'message':'User already exist',
                'email_exist':True
            })
        except ObjectDoesNotExist:
            serializer=UserSerializer(data=request.data)
            if serializer.is_valid():
                user=serializer.save(
                    is_active=False
                )
                user.role='user'
                
                user.save()
                return Response({'message':'Signed up successfully',
                                 'data':UserSerializer(user).data,
                                 'status':status.HTTP_200_OK
                                 })
               





class LoginView(APIView):
    permission_classes=[AllowAny]
    

    def post(self,request):
        email,password=request.data['email'],request.data['password']
        print(email,password)

        try:
            user=User.objects.get(email=str(email).strip().lower())

            if user.check_password(password):
                if user.is_active == True:
                    token=get_tokens_for_user(user)
                    serializer=UserSerializer(user,many=False)
                    return Response({
                        'message':'logged in succesfully',
                        'logged_in':True,
                        'status':status.HTTP_200_OK,
                        'token':token,
                        'data':serializer.data
                    })
                else:
                   return Response({
                    "message":"This Account is not Activated, Check your mail",
                    "status":status.HTTP_200_OK,
                    "logged_in":False
                }) 
            else:
                return Response({
                    "message":"incorrect Email or Password",
                    "status":status.HTTP_404_NOT_FOUND,
                    "logged_in":False
                })
        except ObjectDoesNotExist:
            return Response({
                'message':'User don\'t exist',
                'status':status.HTTP_200_OK,
                'logged_in':False
            })


