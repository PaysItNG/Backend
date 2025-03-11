from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView,DestroyAPIView
from rest_framework.response import Response
# Create your views here.
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny
from userauth.views import getUserData
from main.serializers import *
from main.models import *
from rest_framework.decorators import api_view
import hashlib
import hmac
from django.conf import settings
import json
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from main.paystack import *
from main.serializers import *


no_success_status=['pending','ongoing','queued']





@api_view(['POST'])
def PaystackWebhook(request):
    payload = request.data
    print(payload)
    sig_header = request.headers['x-paystack-signature']

    if sig_header == None:
        return Response({
            'data':'Missing paystack signature',
            'status':'failed'
        })
    
    # print('REQUEST HEADERS ',request.headers)
   
    hash=hmac.new(
                 key=settings.PSTACK_SECRET_KEY.encode('utf-8'),
                  msg=json.dumps(payload).encode(),
                  digestmod=hashlib.sha512
                  ).hexdigest()
    
    # print('%s %s' %(request.headers['x-paystack-signature'],hash))
    # print('%s' %(request.headers))
    if sig_header!= hash:
        print("failed")
        return Response({
            'data':'invalid paystack signature',
            'status':'failed'
        })
    

    
    event_data=json.loads(payload)

    if event_data.get('event') == 'charge.success':
        print('success')
        

        return Response({
            'data':event_data,
            "status": "success"
        })
    




class DepositFundsView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]

    def post(self,request,*args,**kwargs):
        data=request.data['data']
        paystack_refs=[]

        ## REUSEABLE LOGIC TO CHECK IF PAYSTACK REFERENCE ALREADY EXISTS(PROBABLY)

        # for obj in Transaction.objects.all():
        #     if obj.paystack_data != None:
        #         print(json.loads(obj.paystack_data))
        #         ref=json.loads(obj.paystack_data)['data']['reference']
        #         paystack_refs.append(ref)

        try:
            transaction=Transaction.objects.get(paystack_ref=data['reference'])
            return Response({
                'status':'failed',
                'message':'payment reference already assigned'
            })


        except ObjectDoesNotExist:
            response=PaystackVerify(data=data)
            transaction=Transaction()
            status=''
            message=''
            deposited=False
           
            wallet={}
            if response['data']['status'] in no_success_status:
                transaction.status=no_success_status[0]
                deposited=False
                status='failed'
                message='deposit pending'
            else:
                if response['data']['status'] == 'success':
                    transaction.status='completed'
                    user_wallet=Wallet.objects.get(user=request.user)
                    user_wallet.funds+=float(response['data']['amount'])
                    user_wallet.save()
                    wallet=WalletSerializer(user_wallet).data
                    deposited=True
                    status='success'
                    message='deposit successful'


                elif response['data']['status']=='failed':
                    transaction.status = 'failed'
                    deposited=False
                    status='failed'
                    message='deposit failed'
                else:
                    pass
            
            transaction.user=request.user
            transaction.amount=float(response['data']['amount'])
            transaction.transaction_type='deposit'
            transaction.paystack_data=json.dumps(response)
            transaction.save()

            


                

            print(response)
            return Response({
                'transaction':TransactionSerializer(transaction).data,
                'wallet':wallet,
                'status': status,
                'message':message,
                'deposited':deposited

            })





