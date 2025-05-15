from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.decorators import api_view
from rest_framework import status
from django.conf import settings
from .vtpass import VtuServicesUtils,validate_phonenumber
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.response import Response
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny
from main.models import *
import decimal
from main.serializers import *
from . import gsubs
import time
import logging
import threading
networks=['mtn','etisalat','glo','airtel']
logger=logging.getLogger(__file__)

# Create your views here.

VtuPass=VtuServicesUtils()
def transaction_instance(user,transaction_type,status,
                                amount,description,reference_id):
    
    
    transaction=Transaction.objects.create( user=user,
                                            transaction_type=transaction_type,
                                            status=status,
                                            amount=decimal.Decimal(float(amount)),
                                            description=description,
                                            reference_id=reference_id
                                                    )
    logger.debug(transaction)
  
    return transaction




def refund_user(user,amount):
    wallet =Wallet.objects.get(user =user)
    wallet.balance+= decimal.Decimal(float(amount))
    wallet.save()
    
def handle_failed_transaction(user, transaction):
    refund_user(user, transaction.amount)
    transaction.status = 'refunded'
    transaction.save()
    return Response({'detail': 'Transaction failed, user refunded'}, status=status.HTTP_402_PAYMENT_REQUIRED)

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
    def get_user_wallet(self,request):
        wallet=Wallet.objects.get(user=request.user)

        return wallet
    
    def settle_failed_transaction(self,wallet,transaction):
        try:
            if transaction.status == 'refunded':
                logger.info(f"Refund already processed for transaction {transaction.reference_id}")
                return
            
            time.sleep(5)
            wallet.balance +=decimal.Decimal(float(transaction.amount))
            wallet.save()
            transaction.status='refunded'
            transaction.save()
            logger.info(f"Refund successful for transaction {transaction.reference_id}")
            return Response({'data':TransactionSerializer(transaction).data,'message':'refunded'
                            },status=status.HTTP_200_OK)

            

        except Exception as e:
            logger.error(f"Refund failed for transaction {transaction.reference_id}: {str(e)}")


    
   
    

    def get(self,request):
        service_id=str(request.GET.get('service_id')).strip()
        service_type=str(request.GET.get('service_type')).upper()
        if not service_id or not service_type:
            return Response({'error': 'service_id and service_type are required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            if service_type == 'TV':
                res=VtuServicesUtils().GetServiceVariations(service_id=service_id)
                return Response({
                'data':res,
                    }, status=status.HTTP_200_OK)
            if service_type == 'DATA':
                res = gsubs.fetch_data_plans(service_id)
                res2=VtuServicesUtils().GetServiceVariations(service_id=f'{service_id}')
                providers=res+res2
                filtered_providers = [plan for plan in providers if plan.get('price', 0) <= 10000]
                sorted_data=sorted(filtered_providers,key=lambda x: (x['price'],x['qty']=='null'))
                return Response({
                    'data':sorted_data,
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                        'data':"provide service_type",
                    }, status=status.HTTP_404_NOT_FOUND)
            
        except Exception as e:
            return Response({
                'message':'an error occured' + str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    def post(self,request):
        service_type=str(request.data.get('service_type')).strip().upper()
        service_id=str(request.data.get('service_id')).strip()
        phone_no=request.data.get('phone_no')
        
        res={}
      
        transaction_type='subscription',
        data = request.data
        wallet=self.get_user_wallet(request)
        amount=data['price']
        

        if wallet.balance >= decimal.Decimal(float(amount)):
            try:
                if service_type =='AIRTIME':
                    
                    provider=request.data.get('provider').upper()
                    res =VtuServicesUtils.PayForAirtimeService(service_id=service_id,
                                                            amount=amount,
                                                            phone_no=phone_no)
                    
                    vt_request_id=res.get('requestId')
                    unit_price=res['content']['transactions']['unit_price']
                    
                    if res['content']['transactions']['status'] == 'delivered':
                            
                            transaction=transaction_instance(
                                user=request.user,
                                transaction_type=transaction_type,status='completed',
                                amount=unit_price,description=f'{str(amount)} Airtime Top-up successful',
                                vt_request_id=vt_request_id
                            )

                            wallet=Wallet.objects.get(user=request.user)
                            wallet.balance-=round(decimal.Decimal(amount),2)
                            wallet.save()
                            res['data']=TransactionSerializer(transaction).data

                    elif res['content']['transactions']['status'] == 'pending':
                            transaction=transaction_instance(
                            user=request.user,transaction_type=transaction_type,
                            status='pending', amount=unit_price,description=f'{str(amount)} Airtime Top-up pending',
                            vt_request_id=vt_request_id
                                                )
                            res['data']=TransactionSerializer(transaction).data

                    elif res['content']['transactions']['status'] == 'failed':
                            transaction=transaction_instance(
                            user=request.user,transaction_type=transaction_type,
                            status='failed', amount=unit_price,description=f'{str(amount)} Airtime Top-up failed',
                            vt_request_id=vt_request_id
                                                )
                            res['data']=TransactionSerializer(transaction).data

                    else:
                            res['data']={}
            
                elif service_type =='DATA':
           
                    provider=request.data.get('provider').upper()
                    
                    # wallet.balance+= 2000
                    # wallet.save()
                    transaction=Transaction.objects.create( user=request.user,
                                                                transaction_type=transaction_type,
                                                                status='processing',
                                                                amount=decimal.Decimal(float(data['price'])),
                                                                description='Data Bundle purchase',
                                                    )
                    data['request_id'] = transaction.reference_id
                    providers_dict={
                        "GSUB":gsubs.buy_data,
                        "VTPASS":VtuPass.PayForDataService,
                    }
                    response = providers_dict[provider](request.data)
                    wallet.balance -= decimal.Decimal(float(data['price']))
                    wallet.save()
                    transaction.status=response
                    transaction.save()
                    if response=='success':
                        transaction.status="completed"
                        transaction.save()
                        return Response(
                            {'data':{'status':response,"message":'ok'}}, status = status.HTTP_200_OK
                        )
                    else:
                        return Response(
                            {'data':{'status':response,"message":''}}, status = status.HTTP_400_BAD_REQUEST)
                 
                elif service_type == "STATUS": #check status of pending transactions and credit users
                    if service_id=="DATA":
                        try:
                            transaction = Transaction.objects.get(reference_id=data['reference_id'])
                        except Transaction.DoesNotExist:
                            return Response({'detail': 'Invalid reference ID'}, status=status.HTTP_400_BAD_REQUEST)

                        # Check both providers
                        for check_func in [gsubs.verify_transaction_status, VtuPass.verify_transaction_status]:
                            status_result = check_func(request_id=transaction.reference_id)
                            if status_result == 'failed':
                                return handle_failed_transaction(request.user, transaction)
                            elif status_result == 'success':
                                transaction.status="completed"
                                transaction.save()
                                return Response({'detail': 'Transaction succeeded!'}, status=status.HTTP_202_ACCEPTED)

                            else:
                                return Response({'detail': 'Transaction is still pending '}, status=status.HTTP_202_ACCEPTED)
                    else:
                        return Response("invalid service_id on status check")    
                    


                    
    
                elif service_type == 'ELECTRICITY':
                    
                    meter_type=request.data.get('meter_type')
                    meter_no=str(request.data.get('meter_no')).strip()
                    wallet=self.get_user_wallet(request)
                    res,res_status=VtuPass.PayForElectricityService(billers_code=meter_no,
                                                                service_id=service_id,variation_code=meter_type,
                                                                amount=amount,phone_no=phone_no)
                    
                   
                    
                    data=res['content']['transactions']
                    vt_request_id=str(res.get('requestId')).strip()
                    unit_price=data['unit_price']
                    

                    if wallet.balance >= decimal.Decimal(float(amount)):

                        transaction=transaction_instance(
                            user=request.user,
                            transaction_type=transaction_type,status='processing',
                            amount=decimal.Decimal(float(amount)),
                            description=f"{data['product_name']} Prepaid unit purchase Successful",
                            reference_id=vt_request_id
                        )

                        
                        wallet.balance -=decimal.Decimal(float(amount))
                        wallet.save()

                        if res_status in ['completed', 'pending']:
                            transaction.status= res_status
                            transaction.save()
                            data=TransactionSerializer(transaction).data
                            return Response({'data':data,'message':res_status},status=status.HTTP_200_OK)

                        elif res_status == 'failed':
                            transaction.status= res_status
                            transaction.save()
                            threading.Thread(target=self.settle_failed_transaction,
                                args=(wallet,transaction)
                            ).start()

                            return Response({'data':TransactionSerializer(transaction).data,
                                                'massage':'Transaction failed refunds will be processed shortly within 5 seconds'},status=status.HTTP_400_BAD_REQUEST)

                        else:
                            return Response({'data':{}},status=status.HTTP_204_NO_CONTENT)
                    else:
                        return Response({'message':'insufficient fund','data':{}},status=status.HTTP_406_NOT_ACCEPTABLE)
                
                

                elif service_type == 'TV':
                    pass
                return Response({'data':res}, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({'data':f'An error occured {e} with invalid parameters'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response({'data':{'status':"failed",'message':'Insufficient balance'}}, 
                            status = status.HTTP_400_BAD_REQUEST)
                



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