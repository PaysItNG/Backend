from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView
from rest_framework.decorators import api_view
from rest_framework import status
from django.conf import settings
from .vtpass import VtuServicesUtils,validate_phonenumber,generate_vtu_request_id
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
statuses=['success','failed']
tv_services=['dstv','gotv','startimes','showmax']
logger=logging.getLogger(__file__)

# Create your views here.

VtuPass=VtuServicesUtils()
def transaction_instance(user,transaction_type,status,amount,description):
    
    transaction=Transaction.objects.create( user=user,transaction_type=transaction_type,
                                            status=status,amount=decimal.Decimal(float(amount)),
                                            description=description
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
        service_id=str(request.GET.get('service_id')).strip().lower()
        try:
            if service_id in tv_services:
                res=VtuPass.GetServiceVariations(service_id=service_id)
                return Response({
                'data':res,
                    }, status=status.HTTP_200_OK)
            elif service_id in networks:
                res = gsubs.fetch_data_plans(service_id)
                res2=VtuPass.GetServiceVariations(service_id=f'{service_id}-data')
                providers=res+res2
                filtered_providers = [plan for plan in providers if plan.get('price', 0) <= 10000]
                sorted_data=sorted(filtered_providers,key=lambda x: (x['price'],x['qty']=='null'))
                return Response({
                    'data':sorted_data,
                }, status=status.HTTP_200_OK)
            
            else:
                return Response({
                        'data':"Invalid service ID",
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
        transaction_type='subscription'
        data = request.data.copy()
        wallet=self.get_user_wallet(request)
        amount=data.get('price',0)
        verify_transaction_status=[gsubs.verify_transaction_status,VtuPass.verify_transaction_status]
        provider=str(request.data.get('provider')).upper()

        
        
        try:

            if service_type == "STATUS": #check status of pending transactions and credit users
                try:
                        transaction = Transaction.objects.get(reference_id=data['reference_id'])
                except Transaction.DoesNotExist:
                    return Response({'detail': 'Invalid reference ID'}, status=status.HTTP_400_BAD_REQUEST)
                
                if service_id.upper() in ["DATA","AIRTIME"]:
                    
                    # Check both providers
                    idx=0
                    status_result='pending'

                    for idx, check_func in enumerate(verify_transaction_status):
                        try:
                            status_result = check_func(request_id=transaction.reference_id)
                            print(f"Attempt {idx + 1} using {check_func.__name__}: {status_result}")
                            if status_result in statuses:
                                break
                        except Exception as e:
                            print(f"Error in {check_func.__name__}: {e}")
                            continue

                    
                    if status_result == 'failed':
                        return handle_failed_transaction(request.user, transaction)
                    elif status_result == 'success':
                        transaction.status="completed"
                        transaction.save()
                        return Response({'detail': 'Transaction succeeded!'}, status=status.HTTP_202_ACCEPTED)

                    else:
                        return Response({'detail': 'Transaction is still pending '}, status=status.HTTP_202_ACCEPTED)
                
                elif service_id.upper() in ["TV","ELECTRICITY"]:
                    status_result=verify_transaction_status[1](request_id=transaction.reference_id)
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
                        


            if wallet.balance >= decimal.Decimal(float(amount)):
                
                    if service_type =='AIRTIME':

                        transaction=transaction_instance(user=request.user,transaction_type=transaction_type,
                                                            status='processing',amount=decimal.Decimal(float(amount)),
                                                            description=f"Airtime purchase"
                                                            )  
                        data['request_id']=transaction.reference_id
                        res_status =VtuPass.PayForAirtimeService(data)
                        print(res_status)
 
                        # vt_request_id=str(res.get('requestId')).strip()
                        # unit_price=data['unit_price']

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
                            return Response({'data':TransactionSerializer(transaction).data,
                                                'message':'processing'},status=status.HTTP_102_PROCESSING)

                        

                    if service_type =='DATA':
                        
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
                        response = providers_dict[provider](data)
                        print(response)
                        
                        wallet.balance -= decimal.Decimal(float(data['price']))
                        wallet.save()
                        transaction.status=response
                        transaction.save()
                        data=TransactionSerializer(transaction).data
                        if response=='completed':
                            transaction.status=response
                            transaction.save()
                            return Response(
                                {'data':{'status':response,"message":'ok','content':data},}, status = status.HTTP_200_OK
                            )
                        else:
                            return Response(
                                {'data':{'status':response,"message":'','content':data}}, status = status.HTTP_400_BAD_REQUEST)
                        
        
                    if service_type == 'ELECTRICITY':
                        
                        
                        wallet=self.get_user_wallet(request)

                        transaction=transaction_instance(
                            user=request.user,
                            transaction_type=transaction_type,status='processing',
                            amount=decimal.Decimal(float(amount)),
                            description=f"{str(service_id).replace('-',' ').capitalize()} Prepaid unit purchase"
                          
                        )
                        data['request_id']=transaction.reference_id


                        res,res_status=VtuPass.PayForElectricityService(data)
                        

                        wallet.balance -=decimal.Decimal(float(amount))
                        wallet.save()
                        #re assing the description from response received from the response to get acrimony PHED.KEDCO
                        # transaction.description=f'{res['content']['transactions']['product_name']} Prepaid unit purchase'
                        

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
                                                'message':'Transaction failed refunds will be processed shortly within 5 seconds'},status=status.HTTP_400_BAD_REQUEST)

                        else:
                            return Response({'data':TransactionSerializer(transaction).data,
                                                'message':'processing'},status=status.HTTP_102_PROCESSING)
                    
                    

                    if service_type == 'TV':
                        transaction=transaction_instance(
                            user=request.user,
                            transaction_type=transaction_type,status='processing',
                            amount=decimal.Decimal(float(amount)),
                            description=f"{data['service_id']} subscription purchase"
                          
                        )

                        data['request_id']=transaction.reference_id
                        res,res_status=VtuPass.PayForTvService(data)

                        wallet.balance -=decimal.Decimal(float(amount))
                        wallet.save()
                        #re assing the description from response received from the response to get acrimony PHED.KEDCO
                        # transaction.description=f'{res['content']['transactions']['product_name']} Prepaid unit purchase'
                        

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
                            return Response({'data':TransactionSerializer(transaction).data,
                                                'message':'processing'},status=status.HTTP_102_PROCESSING)


                    return Response({'data':res}, status=status.HTTP_200_OK)

                
            else:
                return Response({'data':{'status':"failed",'message':'Insufficient balance'}}, 
                                status = status.HTTP_400_BAD_REQUEST)
            

            


                        
        except Exception as e:
                        return Response({'data':f'An error occured {e} with invalid parameters'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class VerifyNumberView(APIView):
    def post(self,request):
        
        service_id=str(request.data.get('service_id')).strip()
        service_type=str(request.data.get('service_type')).strip()

        try:
            response={}

            if service_type.lower() in ['prepaid','postpaid']:
                meter_no=str(request.data.get('meter_no')).strip()

                response=VtuPass.VerifyMeterNumber(billers_code=meter_no,
                                                            service_id=service_id,
                                                            service_type=service_type
                                                            )
                
                print('DATA', response)
               
                if 'WrongBillersCode' in response['content'] and response['content']['WrongBillersCode']== True:
                    return Response({
                        'data':{},
                        'message':response['content']['error']
                    }, status=status.HTTP_403_FORBIDDEN)
                    
                else:

                    
                    return Response({
                        'data':response['content']
                    },status=status.HTTP_200_OK)
             
            elif service_type.lower() in tv_services:
                card_no=str(request.data.get('card_no')).strip()
                response=VtuPass.VerifySmartCardNumber(card_number=card_no,service_id=service_id)
                if 'WrongBillersCode' in response['content'] and response['content']['WrongBillersCode']== True:
                    
                    return Response({
                        'data':{},
                        'message':response['content']['error']
                    }, status=status.HTTP_403_FORBIDDEN)
                else:

                    
                    return Response({
                        'data':response['content']
                    },status=status.HTTP_200_OK)
            else:
                return Response({
                    'message':'Invalid service ID'
                },status=status.HTTP_406_NOT_ACCEPTABLE)

                              
                
        except Exception as e:
            return Response({
                'message':f'an error occured {e}'
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)







class VtuWebhookView(APIView):
    def post(self,request):
        print('INSIDE WEBBHOOK ',request)
        return Response('ok')