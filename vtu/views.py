from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.decorators import api_view
from rest_framework import status
from django.conf import settings
from .vtpass import *
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny
from main.models import *
import decimal
from main.serializers import *
from . import gsubs



# Create your views here.
def create_transaction_instance(user,payment_type,transaction_type,status,amount,description,vt_request_id):
    transaction=Transaction.objects.create( user=user,payment_type=payment_type,
                                                            transaction_type=transaction_type,
                                                            status=status,
                                                            amount=decimal.Decimal(float(amount)),
                                                            description=description,
                                                            vt_request_id=vt_request_id
                                                )

    return transaction


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



    


class VtuServicesView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    def get(self,request):
        service_id=request.GET.get('service_id')
        service_type=str(request.GET.get('service_type')).upper()
        try:
            
            if service_type == 'TV':
                res=VtuServicesUtils.GetServiceVariations(service_id=service_id)
                return Response({
                'data':res,
                    }, status=status.HTTP_200_OK)
            if service_type == 'DATA':

                res2 = gsubs.fetch_data_plans(service_id)
                
                res=VtuServicesUtils.GetServiceVariations(service_id=f'{service_id}-data')

                
                for item in res['content']['variations']:
                    item['price']=float(item['variation_amount'])*gsubs.data_percentage_add
                    item['provider']='VTPASS'
                    item['plan_id']=str(item['variation_code']).strip()
                    if '30 days' in str(item['name']).lower():
                        item['duration']= 'monthly'
                        size=item['name'].split(' ')
                        item['qty']=VtuServicesUtils.extractDataSize(size)
                        
                    elif 'month' in str(item['name']).lower():
                        item['duration']='monthly'
                        size=item['name'].split(' ')
                        item['qty']=VtuServicesUtils.extractDataSize(size)
                        
                    
                    elif 'week' in  str(item['name']).lower():
                        item['duration']='weekly'
                        size=item['name'].split(' ')
                        item['qty']=VtuServicesUtils.extractDataSize(size)
                    else:

                        item['duration']='daily'
                        size=item['name'].split(' ')
                        item['qty']=VtuServicesUtils.extractDataSize(size)
                for item in res2:
                    item['provider']='GSUBS'

                response_data  ={
                    "provider1":res,
                    "provider2":res2
                }
                
                return Response({
                    'data':response_data,
                }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'message':'an error occured' + str(e),
               
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def post(self,request):
        service_type=str(request.data.get('service_type')).upper()
        service_id=request.data.get('service_id')
        
        phone_no=request.data.get('phone_no')
        res={}
        payment_type='debit',
        transaction_type='subscription',
        try:
            if service_type =='AIRTIME':
                amount=request.data.get('amount')
                res =VtuServicesUtils.PayForAirtimeService(service_id=service_id,
                                                        amount=amount,
                                                        phone_no=phone_no)
                

                
                vt_request_id=res.get('requestId')
                unit_price=res['content']['transactions']['unit_price']

                if res['content']['transactions']['status'] == 'delivered':
                    
                    transaction=create_transaction_instance(
                        user=request.user, payment_type=payment_type,
                        transaction_type=transaction_type,status='completed',
                        amount=unit_price,description=f'{str(unit_price)} Airtime Top-up successful',
                        vt_request_id=vt_request_id
                    )
                    res['data']=TransactionSerializer(transaction).data

                elif res['content']['transactions']['status'] == 'pending':
                    transaction=create_transaction_instance(
                    user=request.user, payment_type=payment_type,transaction_type=transaction_type,
                    status='pending', amount=unit_price,description=f'{str(unit_price)} Airtime Top-up pending',
                    vt_request_id=vt_request_id
                                        )
                    res['data']=TransactionSerializer(transaction).data

                elif res['content']['transactions']['status'] == 'failed':
                    transaction=create_transaction_instance(
                    user=request.user, payment_type=payment_type,transaction_type=transaction_type,
                    status='failed', amount=unit_price,description=f'{str(unit_price)} Airtime Top-up failed',
                    vt_request_id=vt_request_id
                                        )
                    res['data']=TransactionSerializer(transaction).data

                else:
                    res['data']={}

            if service_type =='DATA':


                variation_code=request.data.get('variation_code')
                variation_amount=request.data.get('variation_amount')
                res =VtuServicesUtils.PayForDataService(service_id=service_id,
                                                        phone_no=phone_no,
                                                        variation_code=variation_code)
                
                vt_request_id=res.get('requestId')
                unit_price=res['content']['transactions']['unit_price']
                

                if res['content']['transactions']['status'] == 'delivered':
                    
                    transaction=create_transaction_instance(
                        user=request.user, payment_type=payment_type,
                        transaction_type=transaction_type,status='completed',
                        amount=unit_price,description=f'{str(unit_price)} Data Bundle purchase successful',
                        vt_request_id=vt_request_id
                    )
                    res['data']=TransactionSerializer(transaction).data

                elif res['content']['transactions']['status'] == 'pending':
                    transaction=create_transaction_instance(
                    user=request.user, payment_type=payment_type,transaction_type=transaction_type,
                    status='pending', amount=unit_price,description=f'{str(unit_price)} Data Bundle purchase pending',
                    vt_request_id=vt_request_id
                                        )
                    res['data']=TransactionSerializer(transaction).data

                elif res['content']['transactions']['status'] == 'failed':
                    transaction=create_transaction_instance(
                    user=request.user, payment_type=payment_type,transaction_type=transaction_type,
                    status='failed', amount=unit_price,description=f'{str(unit_price)} Data Bundle purchase failed',
                    vt_request_id=vt_request_id
                                        )
                    res['data']=TransactionSerializer(transaction).data

                else:
                    res['data']={}


            if service_type == 'ELECTRICITY':
                meter_type=request.data.get('meter_type')
                meter_no=str(request.data.get('meter_no')).strip()
                res=VtuServicesUtils.PayForElectricityService(billers_code=meter_no,
                                                              service_id=service_id,variation_code=meter_type,
                                                              amount=amount,phone_no=phone_no)
                vt_request_id=res.get('requestId')
                unit_price=res['content']['transactions']['unit_price']

                if res['content']['transactions']['status'] == 'delivered':
                    transaction=create_transaction_instance(
                        user=request.user, payment_type=payment_type,
                        transaction_type=transaction_type,status='completed',
                        amount=unit_price,description=f'{str(unit_price)} for {res['content']['transactions']['product_name']} Prepaid unit purchase Successful',
                        vt_request_id=vt_request_id
                    )
                    res['data']=TransactionSerializer(transaction).data

                elif res['content']['transactions']['status'] == 'pending':
                    transaction=create_transaction_instance(
                        user=request.user, payment_type=payment_type,
                        transaction_type=transaction_type,status='pending',
                        amount=unit_price,description=f'{str(unit_price)} for {res['content']['transactions']['product_name']} Prepaid unit purchase Pending',
                        vt_request_id=vt_request_id
                    )
                    res['data']=TransactionSerializer(transaction).data

                elif res['content']['transactions']['status'] == 'failed':
                    transaction=create_transaction_instance(
                    user=request.user, payment_type=payment_type,transaction_type=transaction_type,
                    status='failed', amount=unit_price,description=f'{str(unit_price)} for {res['content']['transactions']['product_name']} Prepaid unit purchase Failed',
                    vt_request_id=vt_request_id
                                        )
                    res['data']=TransactionSerializer(transaction).data

                else:
                    res['data']={}


            if service_type == 'TV':
                pass
            return Response({'data':res}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'data':f'An error occured {e} with invalid parameters'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class VerifyMeterNumberView(APIView):
    def post(self,request):
        meter_no=str(request.data.get('meter_no')).strip()
        service_id=str(request.data.get('service_id')).strip()
        service_type=str(request.data.get('service_type')).strip()

        try:

            response=VtuServicesUtils.VerifyMeterNumber(billers_code=meter_no,
                                                        service_id=service_id,
                                                        service_type=service_type
                                                        ) 
        
            if 'WrongBillersCode' in response['content']:
                if response['content']['WrongBillersCode']== True:
                    return Response({
                        'data':{},
                        'message':response['content']['error']
                    }, status=status.HTTP_200_OK)
            else:

                
                return Response({
                    'data':response['content']
                },status=status.HTTP_200_OK)          
            
        except Exception as e:
            return Response({
                    'message':f'an error occured {e}'
                },status=status.HTTP_500_INTERNAL_SERVER_ERROR)







class VtuWebhookView(APIView):
    def post(self,request):
        print('INSIDE WEBBHOOK ',request)
        return Response('ok')