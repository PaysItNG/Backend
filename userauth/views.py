from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView,ListCreateAPIView
from main.serializers import *
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import (AllowAny,
                                        IsAuthenticated,
                                        
                                        IsAuthenticatedOrReadOnly,
                                        IsAdminUser)
from rest_framework.response import Response
from rest_framework import generics,viewsets,status
from django.core.exceptions import ObjectDoesNotExist
from main.models import *
from django.contrib.auth.hashers import check_password
import requests
from django.conf import settings
# Create your views here.
from rest_framework.decorators import api_view, permission_classes
import logging
from django.shortcuts import get_object_or_404
import datetime
from main.models import generateinviteID
from main.emailsender import sendmail
from rest_framework import status

import string
import random
from django.utils import timezone

logger=logging.getLogger(__file__)
PaysTack =PayStackUtils()

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def generateidentifier(length)->str:
    char=string.ascii_lowercase+string.digits
    token="".join(random.choice(char) for _ in range(length))

    return token

def requestUrl(request)->str:
    scheme = request.is_secure() and "https" or "http"
    url=f'{scheme}://{request.get_host()}'
    return url


def getUserData(request):
    objects={}
    try:
        user=UserSerializer(User.objects.get(id=request.user.id),many=False).data
    except ObjectDoesNotExist:
        user=[]
    try:
        profile=UserProfileSerializer(UserProfile.objects.get(user=request.user),many=False).data
    except ObjectDoesNotExist:
        profile=[]
    
    objects['user']=user
    objects['profile']=profile

    return objects




class SignupView(APIView):
    serializer_class = UserSerializer
    permission_classes = (AllowAny,)

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'message': 'Email is required', 'status': 'error'}, status=status.HTTP_400_BAD_REQUEST)
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            return Response({'message': 'User already exists', 'email_exist': True}, status=status.HTTP_400_BAD_REQUEST)
        # Serialize and validate user data
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(role='user', is_active=False)
            raw_otp = generate_otp()
            otp_hash = hash_otp(raw_otp)
            OTP.objects.create(
                user=user,
                otp_hash=otp_hash,
                expires_at=timezone.now() + timezone.timedelta(minutes=5)
            )

            # Send OTP via email
            send_user_message(
                "Your OTP Code",
                f"Your OTP code is {raw_otp}. It will expire in 5 minutes.",
                user
            )
            return Response({
                'status':status.HTTP_200_OK,
                'message':'User already exist',
                'email_exist':True
            })
        except ObjectDoesNotExist:
            serializer=UserSerializer(data=request.data)
            token=generateinviteID(5)

            try:
                User.objects.get(token=token)
            except User.DoesNotExist:
                if serializer.is_valid():
                    user=serializer.save()
                    user.role='user'
                    user.is_active=False
                    user.token=token
                    
                    user.save()
                    return Response({'message':'Signed up successfully',
                                    'data':UserSerializer(user).data,
                                    'status':status.HTTP_200_OK,
                                    'otp':token
                                    })
                else:
                    return Response({
                        'message':'invalid data',
                        'status':'error'
                    })
               



class VerifyActiveStatusView(APIView):
    def post(self,request,*args,**kwargs):
        token=str(request.data.get('otp')).strip()
        try:
            user=User.objects.get(token=token)
            if user.is_active == True:
                
                serializer=UserSerializer(User.objects.get(user=user),many=False).data
                return Response({
                    'data':serializer,
                    'status':True,
                    'message':'This user account has been activated already'

                })
            else:
                user.is_active=True
                user.save()
                serializer=UserSerializer(user).data

                return Response({
                    'data':serializer,
                    'status':True,
                    'message':'Account successfully activated'

                })

        except ObjectDoesNotExist:
            return Response({
                'data':{},
                'message':'user profile don\'t exist',
                'status':False
            })

class LoginView(APIView):
    permission_classes=[AllowAny]
    def post(self,request):
        email,password=request.data['email'],request.data['password']
        # print(email,password)

        try:
            user=User.objects.get(email=str(email).strip().lower())
            print(user)

            if user.check_password(password):
                if user.is_active == True:
                    token=get_tokens_for_user(user)
                    serializer=UserSerializer(user,many=False).data
                    # print(serializer['profile'])
                    serializer['profile']=UserProfileSerializer(
                        UserProfile.objects.get(id=serializer['profile']),many=False).data
                   
                    return Response({
                        'message':'logged in succesfully',
                        'logged_in':True,
                        'status':status.HTTP_200_OK,
                        'token':token,
                        'data':serializer
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

@api_view(['POST'])
@permission_classes([AllowAny])
def VerifySocialLogin(request):
    scheme = request.is_secure() and "https" or "http"
    url=f'{requestUrl(request)}/oauth/convert-token/'
    print(url)
    token=request.data.get('access_token')
    # print(token)


    data={
        'grant_type':'convert_token',
        'token':token,
        'client_id': settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
        'backend':'google-oauth2',
        
    }

    response=requests.post(url,data=data)
    logger.debug(response)
    print(response.json())

    return Response({
        'data':response.json()
    })


class RequestPasswordChangeView(APIView):
    
    permission_classes=[AllowAny]
    serializer_class=SecuritySerializer

    def post(self,request):
        email=request.data.get('email')
        try:
            user=User.objects.get(email=email)

            try:
                security=Security.objects.get(user=user)
                generate_token=generateidentifier(20)
                
                token=make_password(generate_token)
                security.token=generate_token
                security.save()
                data={'token':token,
                      'data':SecuritySerializer(security,many=False).data,
                      'url':f'{requestUrl(request)}/auth/password/verify?q={generate_token}'
                      }
            except ObjectDoesNotExist:
                security=Security.objects.create(user=user)
                security.refresh_from_db()
                generate_token=generateidentifier(20)
                
                token=make_password(generate_token)
                security.token=generate_token
                security.save()

                data={'token':generate_token,
                      'data':SecuritySerializer(security,many=False).data,
                      'url':f'{requestUrl(request)}/auth/password/verify?q={generate_token}'
                      }


            message = """<p>Hi there!, <br> <br>You have requested to change your password. <br> <br>
            <b>Use """ + generate_token + """ as your verification code</b></p>"""
            subject = 'Password Change Request'
            # sendmail([user.email],message,message,subject)
            return Response(data,status=status.HTTP_202_ACCEPTED)
            

        except ObjectDoesNotExist:
            return Response({
                'message':'user with email don\'t exist',
                'status':status.HTTP_404_NOT_FOUND,
                'user':False
            })
        
class VerifyPasswordRequestChangeView(APIView):
    permission_classes=[AllowAny]
    serializer_class=SecuritySerializer
    def post(self,request):
        q=str(request.GET.get('q')).strip()
       
        try:
            security=Security.objects.get(token=q)
            now=timezone.now()
            security_time=security.date_created
            
            if ((now-security_time).seconds < 60):
                new_password=request.data.get('new_password')
                security.user.set_password(new_password)
                security.user.save()

                return Response({
                    'message':'Password Change Successfully',
                    'status':status.HTTP_200_OK,
                    'verified':True
                })
            else:
                return Response({
                    'message':'this link has elasped it\'s duration',
                    'status':status.HTTP_200_OK,
                    'verified':False
                })
        except ObjectDoesNotExist:
            return Response({
                'verified': False,
                'message':'Not found',
                'status':status.HTTP_404_NOT_FOUND
            })

        
        

        
class KycVerificationView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    serializer_class=KYCVerificationSerializer

    def get(self,*args,**kwargs):
        data=getUserData(self.request)
        try:
            kyc_data=KYCVerificationSerializer(
                KYCVerification.objects.get(user=self.request.user),
                many=False
            ).data

            data['kyc']=kyc_data
            return Response({
                'data':data,
                'status':status.HTTP_200_OK
            })
        except:
            return Response({
                'data':[],
                'message':'No KYC status yet',
                'status':status.HTTP_404_NOT_FOUND
            })

    def put(self,*args,**kwargs):
        serializer=KYCVerificationSerializer(data=self.request.data)

        if serializer.is_valid():
            serializer.save(
                user=self.request.user,
                submitted_at=timezone.now(),
                status='pending',
                submitted=True
            )

            return Response({
                'data':KYCVerificationSerializer(serializer).data,
                'status':status.HTTP_200_OK,
                'message':'Successfully sent'
            })
        else:
            return Response({
                'status':status.HTTP_404_NOT_FOUND,
                'message':'invalid valid'
            })

            


    