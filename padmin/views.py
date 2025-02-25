from django.shortcuts import render

# Create your views here.
from django.contrib.auth import login,logout,authenticate
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import (AllowAny,
                                        IsAuthenticated,
                                        
                                        IsAuthenticatedOrReadOnly,
                                        IsAdminUser)
from userauth.models import *
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from main.emailsender import sendmail
from main import models as mmodels
from main.decorators import *
from main.serializers import *




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


        


class AdminLoginView(APIView):
    authentication_classes=[AllowAny]

    def post(self,request,*args,**kwargs):
        pass