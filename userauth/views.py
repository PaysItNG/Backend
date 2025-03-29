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
from .signals import send_user_message
from payment.utils import PayStackUtils

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
    permission_classes = [AllowAny]

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
            raw_otp = generate_otp(6)
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
                'message': 'Signup successful. OTP sent to email.',
                'status': status.HTTP_200_OK,
                'data': UserSerializer(user).data
            }, status=status.HTTP_200_OK)
        return Response({'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
               


class VerifyOTPView(APIView):
    permission_classes=[]
    def post(self, request):
        otp = request.data.get("otp")
        email = request.data.get("email")
        if not otp or not email:
            return Response({"message": "OTP and email are required", "status": False}, status=400)
        try:
            user = User.objects.get(email=email)
            hashed_otp = hashlib.sha256(otp.encode()).hexdigest()
            otp_instance = OTP.objects.filter(user=user, otp_hash=hashed_otp).first()
            if not otp_instance:
                return Response({"message": "Invalid OTP", }, status=status.HTTP_400_BAD_REQUEST)
            if otp_instance.is_expired():
                
                raw_otp = generate_otp(6)
                otp_hash = hash_otp(raw_otp)
                otp,_ =OTP.objects.get_or_create(
                    user=user)
                otp.otp_hash=otp_hash,
                otp.expires_at=timezone.now() + timezone.timedelta(minutes=5)
                otp.save()
                send_user_message(
                        "Your OTP Code",
                        f"Your OTP code is {raw_otp}. It will expire in 5 minutes.",
                        user
                            )
                return Response({"message": "OTP has expired, check your email for new one", }, status=status.HTTP_400_BAD_REQUEST)
            user.is_active = True
            user.save()
            otp_instance.delete()
            dva_account = PaysTack.create_customer_and_virtual_account(user.email,user.first_name,user.last_name,user.phone_number) 
            return Response({"message": "OTP verified successfully", },status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        
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
                'status':status.HTTP_404_NOT_FOUND,
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
        otp=OTP()
        try:
            user=User.objects.get(email=email)
            try: 
                raw_otp=otp.objects.filter(user).first()
                
                data={'data':UserSerializer(user,many=False).data,
                    'otp':raw_otp,
                    'message':'An OTP have been sent to this mail please check your mail, you can only request for another after 60 seconds'
                    #   'url':f'{requestUrl(request)}/auth/password/verify?q={raw_otp}'
                      }
               
            except ObjectDoesNotExist:
                raw_otp=otp.create_otp(user,
                                       duration='seconds',
                                       value=60)   
                
                data={
                    'data':UserSerializer(user,many=False).data,
                    'otp':raw_otp,
                    'message':'Password request successful, check your mail'
                    #   'url':f'{requestUrl(request)}/auth/password/verify?q={raw_otp}'
                      }


            message = """<p>Hi there!, <br> <br>You have requested to change your password. <br> <br>
            <b>Use """ + raw_otp + """ as your verification code</b></p>"""
            subject = 'Password Change Request'
            send_user_message(
                    "Your OTP Code",
                    f"Your OTP code is {raw_otp}. It will expire in 60 seconds.",
                    user
                )
               
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
    def get(self,request):
        try:
            user=User.objects.get(email=str(request.data.get('email')).strip().copy())

            token=str(request.data.get('otp')).strip()
            otp=OTP.objects.filter(user=user)
            if otp.exists():
                otp=otp.first()
                if otp.otp_hash == hash_otp(token):
                    if otp.is_expired():
                        return Response ({'is_valid':True,'expired':True},status=status.HTTP_406_NOT_ACCEPTABLE)
                    
                    return Response({'is_valid':True,'expired':False,'data':UserSerializer(user,many=False).data,},
                                    status=status.HTTP_202_ACCEPTED)
                else:
                    return Response({
                         'is_valid':False,
                         'message':'invalid OTP'

                    }, status=status.HTTP_406_NOT_ACCEPTABLE)
            else:
                return Response({
                    'message':'no OTP assigned to user'
                },status=status.HTTP_404_NOT_FOUND)

            
        except ObjectDoesNotExist:
            return Response({
                'data':{},
                'message':'Incorrect User email',

            },status=status.HTTP_404_NOT_FOUND)
        

        

    def post(self,request):
        email=str(request.GET.get('email')).strip().copy()
        password1=str(request.data.get('password1')).strip()
        password2=str(request.data.get('password2')).strip()
       
        try:
            user=User.objects.get(email=email)
            if password1 == password2:

                user.set_password(password1)
                user.save()
            

                return Response({
                    'message':'Password Change Successfully',
                    'status':status.HTTP_200_OK,
                    'verified':True
                })
            else:
                return Response({
                'message':'Password don\'t corresponds',
                    'status':status.HTTP_406_NOT_ACCEPTABLE,
                    'verified':False
            })
            
        except ObjectDoesNotExist:
            return Response({
                'verified': False,
                'message':'Not found',
                'status':status.HTTP_404_NOT_FOUND
            })

        
        
class EnableTwoFactorAuthentication(APIView):
    def get(self,request):
        objects=getUserData(request=request)
        user=User.objects.get(email=objects['user']['email'])

        

        
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
            serialized_data=serializer.save(
                user=self.request.user,
                submitted_at=timezone.now(),
                status='pending',
                submitted=True
            )

            return Response({
                'data':KYCVerificationSerializer(serialized_data).data,
                'status':'success',
                'message':'Successfully sent'
            })
        else:
            return Response({
                'status':'failed',
                'message':'invalid valid'
            })

            


    