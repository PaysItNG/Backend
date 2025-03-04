from django.shortcuts import render

# Create your views here.
from django.contrib.auth import login,logout,authenticate
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import (AllowAny,
                                        IsAuthenticated,
                                        
                                        IsAuthenticatedOrReadOnly,
                                        IsAdminUser)
from userauth import models as umodels
from userauth.serializers import *
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from main.emailsender import sendmail
from main import models as mmodels
from main.decorators import *
from main.serializers import *
from datetime import timedelta
from django.utils import timezone



def DurationDifference(s=0,m=0,h=0,d=0):
    return timezone.now()-timedelta(days=d,seconds=s,hours=h,minutes=m)

class AdminLoginView(APIView):
    authentication_classes=[AllowAny]

    def post(self,request,*args,**kwargs):
        pass


class SendRoleInvite(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]
    serializer_class=[RoleInviteSerializer]

    
    @SuperAdminAccess
    def post(self,request,*args,**kwargs):
        role=request.GET.get('role')
        email=str(request.data['email']).strip().lower()
        # url=request.get_full_path()
        scheme = request.is_secure() and "https" or "http"
        url=f'{scheme}://{request.get_host()}/role/invite/accept'

        print(url)
        
        role_invite=mmodels.RoleInvite.objects.create(
            email=email,
            role=str(role).strip().lower()
        )

        body=f'<h2>Hello you\'ve been assigned the role of an {role} on paysit kindly click the link below to accept this invitation thanks</br> {url}</h2>'
        sender={
            'email':'paysit@info.com',
            'name':'paysit'
        }
        sendmail(email,BODY_TEXT=body,
                 BODY_HTML='',
                 SUBJECT='Paysit Role Invitation',
                 email='paysit@info.com',
                 name='paysit'
                 )
        
        return Response({
            'message':'Invitation sent successfully',
            'success':True
        })


class AcceptRoleInvite(APIView):
    permission_classes=[AllowAny]
    def post(self,request):
        identifier=request.GET.get('q')
        try:
            user=RoleInvite.objects.get(identifier=identifier)

            user.user.role=user.role
            user.user.save()
            return Response({
                'status':status.HTTP_200_OK,
                'role_assigned':True,
                'message':'Role assigned successfully'
            })
        except ObjectDoesNotExist:
            return Response({
                'status':status.HTTP_200_OK,
                'role_assigned':False,
                'message':'NO identifier linked to this invitaion'
            })


class KycStatusView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]


    @AllowedUsers(allowed_roles=['admin1','admin'])
    def get(self,request,*args,**kwargs):
        # FILTER BY STATUS AND  DURATIONS
        kyc_status=request.data.get('kyc_status','')
        seconds=int(request.data.get('s',0))
        mins=int(request.data.get('m',0))
        hours=int(request.data.get('hr',0))
        days=int(request.data.get('d',0))

        

        if kyc_status == '':
            duration_delta=DurationDifference(seconds,mins,hours,days)
            data=list(umodels.KYCVerification.objects.all().order_by('-submitted_at'))

            kyc_data=list(filter(lambda x: duration_delta<x.submitted_at<timezone.now(),data))
            print(kyc_data) 
            serialized_data=KYCVerificationSerializer(kyc_data
                    ,many=True).data,
            
            # TO BE MODIFIED
            for serializer in serialized_data[0]:
       
                serializer['user']=UserSerializer(
                    umodels.User.objects.get(id=serializer['user']),many=False
                ).data

            return Response({
                'data': serialized_data,
                'status':'success'
            })
        else:
            duration_delta=DurationDifference(seconds,mins,hours,days)
            users=list(umodels.KYCVerification.objects.all().order_by('-submitted_at'))
            kyc_users=list(filter(lambda x: x.status == kyc_status and duration_delta<x.submitted_at<timezone.now(),users))
            serializer=KYCVerificationSerializer(kyc_users,many=True).data,
            


            # TO BE MODIFIED
            if serializer[0] != []:
                data=serializer[0][0]
                data['user']=UserSerializer(
                        umodels.User.objects.get(id=data['user']),many=False
                    ).data
            else: pass

            print(serializer[0])
            

            return Response({
                'data':serializer,
                'status':'success'

            })



class ApproveKycView(APIView):
    authentication_classes=[JWTAuthentication]
    permission_classes=[IsAuthenticated]

    @AllowedUsers(allowed_roles=['admin1','admin'])
    def get(self,request,id,*args,**kwargs):
        try:

            kyc=KYCVerification.objects.get(id=id)
            serializer=KYCVerificationSerializer(kyc,many=False).data
            serializer['user']=UserSerializer(umodels.User.objects.get(id=serializer['user']),many=False).data

            return Response({
                'data':serializer,
                'status':'ok'
            })
        except ObjectDoesNotExist:
            return Response({
                'status':'error',
                'message':'not kyc data',
                'data':[]
            })


    @AllowedUsers(allowed_roles=['admin1','admin','staff'])
    def put(self,request,id,*args,**kwargs):
        status=request.data.get('status')
        try:

            kyc=KYCVerification.objects.get(id=id)
            kyc.status=status
            kyc.save()
            serializer=KYCVerificationSerializer(kyc,many=False).data
            serializer['user']=UserSerializer(umodels.User.objects.get(id=serializer['user']),many=False).data

            return Response({
                'data':serializer,
                'status':'ok'
            })
        except ObjectDoesNotExist:
            return Response({
                'status':'error',
                'message':'not kyc data',
                'data':[]
            })
    