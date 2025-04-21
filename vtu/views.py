from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.decorators import api_view
from rest_framework import status
from django.conf import settings
from .utils import *
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny

# Create your views here.
class ValidateNumberView(APIView):
    def post(self,request):
        phone_no=request.data.get('phone_no')
        try:
            network_provider,number_valid=validate_phonenumber(phone_no)
            return Response({
                'valid':number_valid,
                'phone_number':phone_no,
                'network_provider':network_provider
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'valid':False,
                'network_provider':''
               
            }, status=status.HTTP_404_NOT_FOUND)


class GetServiceVariationsView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    def get(self,request):
        service_id=request.data.get('service_id')
        try:
        
            res=VtuServicesUtils.GetServiceVariations(service_id=service_id)

         
            for item in res['content']['variations']:
                if '30 days' in str(item['name']).lower():
                    item['duration']='monthly'
                elif 'month' in str(item['name']).lower():
                    item['duration']='monthly'
                elif 'week' in  str(item['name']).lower():
                    item['duration']='weekly'
                else:

                    item['duration']='daily'

            return Response({
                'data':res
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message':'an error occured' + str(e),
               
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
