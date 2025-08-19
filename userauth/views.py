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
from payment.models import DedicatedAccount
from rest_framework.parsers import FileUploadParser,FormParser,MultiPartParser,JSONParser
from django.db import DatabaseError,IntegrityError,OperationalError
from social_django.utils import psa
from django.contrib.auth import authenticate

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

        try:
            email = str(request.data.get('email', '')).strip().lower()
            if not email:
                return Response({'message': 'Email is required', 'status': 'error','status':status.HTTP_400_BAD_REQUEST},
                                status=status.HTTP_400_BAD_REQUEST)
            # Check if user already exists
            if User.objects.filter(email=email).exists():
                return Response({'message': 'User already exists', 'email_exist': True,'status':status.HTTP_400_BAD_REQUEST},
                                status=status.HTTP_400_BAD_REQUEST)
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

                """
                Email sender
                """
                send_user_message(
                    "Your OTP Code",
                    f"Your OTP code is {raw_otp}. It will expire in 5 minutes.",
                    user
                )
                return Response({
                    'message': 'Signup successful. OTP sent to email.',
                    'otp':raw_otp,
                    'status': status.HTTP_200_OK,
                    'data': UserSerializer(user).data
                }, status=status.HTTP_200_OK)
            return Response({'message': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        
        except  DatabaseError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except  IntegrityError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except  OperationalError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

def get_bank_account_or_create(user):
    account = DedicatedAccount.objects.filter(user=user)
    if account.exists():
        return True
    return PaysTack.create_customer_and_virtual_account(user.email,user.first_name,user.last_name,user.phone_number,preferred_bank="sterling-bank")
                  


class VerifyOTPView(APIView):
    permission_classes=[]
    
    def post(self, request):
        otp = request.data.get("otp")
        email = request.data.get("email")
        if not otp or not email:
            return Response({"message": "OTP and email are required", "status": False}, status=status.HTTP_406_NOT_ACCEPTABLE)
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

                """
                Email sender
                """
                send_user_message(
                        "Your OTP Code",
                        f"Your OTP code is {raw_otp}. It will expire in 5 minutes.",
                        user
                            )
                return Response({"message": "OTP has expired, check your email for new one", }, status=status.HTTP_400_BAD_REQUEST)
            user.is_active = True
            user.save()
            otp_instance.delete()
            # get_bank_account_or_create(user)
            return Response({"message": "OTP verified successfully", },status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({"message": "User not found"}, status=status.HTTP_404_NOT_FOUND)


class LoginView(APIView):
    permission_classes=[AllowAny]
    def post(self,request):
        email,password=request.data['email'],request.data['password']
        try:
            user=User.objects.get(email=str(email).strip().lower())

            if user.check_password(password):
                if user.is_active == True:
                    token=get_tokens_for_user(user)
                    serializer=UserSerializer(user,many=False).data
                    serializer['profile']=UserProfileSerializer(
                        UserProfile.objects.get(id=serializer['profile']),many=False).data
                    #get_bank_account_or_create(user)
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
        except  DatabaseError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except  IntegrityError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except  OperationalError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([AllowAny])
@psa()
def VerifySocialLogin(request, backend):
    scheme = request.is_secure() and "https" or "http"
    url=f'{requestUrl(request)}/oauth/convert-token/'
    token=request.data.get('access_token')

    user = request.backend.do_auth(token)
    print(user,user.first_name)


    if user:
        # new_user=User.objects.get(user=user)
        print(user)
        user,_=User.objects.get_or_create(
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            is_active=True

            )
        print(user)
        
        token=get_tokens_for_user(user)
        print(token)
        
        return Response(
            {
                'token': token,
                'user':UserSerializer(user,many=False).data
            },
            status=status.HTTP_200_OK,
            )
    else:
        return Response(
            {
                'errors': {
                    'token': 'Invalid token'
                    }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class RequestVerifyPasswordChangeView(APIView):
    
    permission_classes=[AllowAny]
    serializer_class=SecuritySerializer
    duration=60

    def get(self,request):
        email=request.data.get('email')
        otp=OTP()
        raw_otp=''
        duration=self.duration
        try:
            
            user=User.objects.get(email=email)
            
            profile,_=UserProfile.objects.get_or_create(user=user)
            #  Check if previous otp exists and expired
        
            if profile.otp is not None:
                    
                    # otps= list(filter(lambda x : x.remove_otp_with_due_range(duration=60) == True,otps))
            
                if  profile.otp.is_expired():
                    
                    """
                        Get  or create user security status 
                        check if assigned otp is expired, delete and reassign new one
                        
                        """
                    profile.otp.delete()
                    raw_otp,otp_instance=otp.create_otp(user=user,duration=duration)

                    profile.otp=otp_instance
                    profile.save()

                    """
                    Email sender
                    """ 
                    data={
                        'data':UserSerializer(user,many=False).data,'otp':raw_otp,
                        'message':'Password request successful, check your mail'
                        #   'url':f'{requestUrl(request)}/auth/password/verify?q={raw_otp}'
                        }      
                else:
                    
                    data={'data':UserSerializer(user,many=False).data,        
                        'message':"""An OTP have been sent to this mail kindly check your mail,
                        you can only request for another after 60 seconds""",
                                                }
            

            else:

                # Create and assing otp
                
                raw_otp,otp_instance=otp.create_otp(user=user,duration=duration)
                profile.otp=otp_instance
                profile.save() 

                data={
                    'data':UserSerializer(user,many=False).data,
                    'otp':raw_otp,
                    'message':'Password request successful, check your mail'
                    }

                """
                Email sender
                """
                # message = """<p>Hi there!, <br> <br>You have requested to change your password. <br> <br>
                # <b>Use """ + raw_otp + """ as your verification code</b></p>"""
                # subject = 'Password Change Request'
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
        
        except  DatabaseError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except  IntegrityError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except  OperationalError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        
    def post(self,request):
        try:
            user=User.objects.get(email=str(request.data.get('email')).strip())

            token=str(request.data.get('otp')).strip()
            password1=str(request.data.get('password1')).strip()
            password2=str(request.data.get('password2')).strip()
            profile=UserProfile.objects.get(user=user)
            duration=self.duration
           
                
            if profile.otp.otp_hash == hash_otp(token):
                if profile.otp.is_expired():
                    return Response ({'is_valid':True,'expired':True},status=status.HTTP_406_NOT_ACCEPTABLE)
            
                else:
                    
                    if password1 == password2:

                        user.set_password(password1)
                        user.save()
                        profile.otp.delete()
                        return Response({
                            'message':'Password Change Successfully',
                            'verified':True,'is_valid':True,'expired':False,
                            'data':UserSerializer(user).data
                        },status=status.HTTP_202_ACCEPTED)
                    else:
                        return Response({
                        'message':'Password don\'t corresponds',
                            'status':status.HTTP_406_NOT_ACCEPTABLE,
                            'verified':False
                    })
                    
            else:
                        return Response({
                            'is_valid':False,
                            'message':'invalid OTP'

                        }, status=status.HTTP_406_NOT_ACCEPTABLE)
            
        except User.DoesNotExist:
            return Response({
                'data':{},
                'message':'Incorrect User email',

            },status=status.HTTP_404_NOT_FOUND)
        

        except  DatabaseError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except  IntegrityError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except  OperationalError as e:
            return Response({
                'message':f'an error occured at {e}',
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        

    
        
class EnableTwoFactorAuthentication(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    duration=40
    def get(self,request):
        objects=getUserData(request=request)
        user=User.objects.get(email=objects['user']['email'])
        duration=self.duration
        otp=OTP()

        try:    
            """
            Get  or create user security status 
            check if assigned otp is expired, delete and reassign new one
            
            """
            security,_=Security.objects.get_or_create(user=user)
            if security.otp is not None: 
                    # otps= list(filter(lambda x : x.remove_otp_with_due_range(duration=40) == True,otps))     
                if security.otp.is_expired():
                    security.otp.delete()
                    raw_otp,otp_instance=otp.create_otp(user=user,duration=duration)

                    security.otp=otp_instance
                    security.save()
                    objects['security']=SecuritySerializer(security).data

                    """
                    Email sender
                    """

                    return Response({
                        'success':True,
                        'message':f'An OTP was sent to your mail to validate to Two-Factor Authentication request which expires {str(duration)} seconds',
                        'otp':raw_otp,
                        'data':objects
                    },status=status.HTTP_200_OK)

            
                else:
                    
                    return Response({
                        'success':True,
                        'message':f"""An OTP was sent to this mail kindly check your mail,
                            you can only request for another after {str(duration)} seconds""",
                        'data':objects,

                    },status=status.HTTP_200_OK)
     
            else:
                raw_otp,otp_instance=otp.create_otp(user=user,duration=duration)
                security.otp=otp_instance
                security.save()

                """
                Email sender
                """
                return Response({
                        'success':True,
                        'message':f' OTP  sent to your mail to validate to Two-Factor Authentication request which expires {str(duration)} seconds',
                        'otp':raw_otp,
                        'data':objects
                    },status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'message':f'An error occured {e}',
                'data':{},
                'success':False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        


    def post(self,request):
        otp=str(request.data.get('otp')).strip()
        duration=self.duration

        # otps=[obj for obj in OTP.objects.filter(user=request.user) if obj.remove_otp_with_due_range(duration=40)==True]
        try:
            security=Security.objects.get(user=request.user)

            if security.otp is not None:

                if security.otp.is_expired():
                    return Response ({'is_valid':True,'expired':True,
                                    'message':'This OTP  is expired',
                                    },status=status.HTTP_406_NOT_ACCEPTABLE)
                else:
                    if security.otp.otp_hash == hash_otp(otp):
                        
                        security.two_factor_auth_enabled=True
                        security.otp.delete()
                        security.save()

                       

                        return Response ({'is_valid':True,'expired':False,
                                    'message':'2FA enabled',
                                    },status=status.HTTP_200_OK)
                    else:
                        return Response ({'is_valid':False,
                                    'message':'Invalid OTP',
                                    },status=status.HTTP_200_OK)
            else:
                pass

        except Exception as e:
            return Response({
                'message':f'An error occured {e}',
                'data':{},
                'success':False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






        
class KycVerificationView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    serializer_class=KYCVerificationSerializer
    parser_classes=[MultiPartParser,FormParser]

    def get(self,*args,**kwargs):
        data=getUserData(self.request)
        try:
            kyc_data=KYCVerificationSerializer(
                KYCVerification.objects.get(user=self.request.user),
                many=False
            ).data

            data['kyc']=kyc_data
            return Response({'data':data,'status':status.HTTP_200_OK })
        except:
            return Response({
                'data':[],
                'message':'No KYC status yet',
                'status':status.HTTP_404_NOT_FOUND
            })

    def put(self,*args,**kwargs):
        kyc=KYCVerification.objects.get(user=self.request.user)
        serializer=self.serializer_class(kyc,data=self.request.data)
        

        if serializer.is_valid():
            serialized_data=serializer.save(
               
                # submitted_at=timezone.now(),
                # status='pending',
                submitted=True
            )

            return Response({
                'data':self.serializer_class(serialized_data).data,
                'status':'success',
                'message':'Successfully sent'
                
            })
        else:
            return Response({
                'status':'failed',
                'message':'invalid valid'
            })

            


    
