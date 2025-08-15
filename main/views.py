from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView,DestroyAPIView
from rest_framework.response import Response
# Create your views here.
from rest_framework.decorators import api_view

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny
from userauth.views import getUserData
from .serializers import *
from rest_framework import status
from payment import models as pmodels
from payment.serializers import DedicatedAccountSerializer
from datetime import datetime
from userauth.signals import send_user_message


def AllObjects(user):
    objects={}
    try:
        transaction=Transaction.objects.filter(user=user)
        objects['transaction']=TransactionSerializer(transaction,many=True).data
    except:
        objects['transaction']=[]

    try:
        wallet=Wallet.objects.get(user=user)
        objects['wallet']=WalletSerializer(wallet,many=False).data
    except:
        objects['wallet']=[]

    try:
        kyc=KYCVerification.objects.filter(user=user)
        objects['kyc']=KYCVerificationSerializer(kyc,many=False).data
    except:
        objects['kyc']=[]

    
    try:
        dva=pmodels.DedicatedAccount.objects.filter(user=user).first()
        objects['dva']=DedicatedAccountSerializer(dva,many=False).data
    except:
        objects['dva']=[]

    try:
        card=Card.objects.filter(user=user,issued=True).first()
        objects['card']=Cardserializer(card,many=False).data
    except:
        objects['card']=[]

    return objects

class UserProfileDataView(APIView):
    serializer_class=UserProfileSerializer
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def get(self,request,*args,**kwargs):
        try:
            allObjects=AllObjects(request.user)
            profile=UserProfile.objects.get(user=request.user)
            serializer=self.serializer_class(profile,many=False).data


            serializer['user']=UserSerializer(User.objects.get(id=serializer['user']),many=False).data
            serializer['allObjects']=allObjects

            return Response({
                'data':serializer
            },status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'message':e,
                'data':{},

            },status=status.HTTP_404_NOT_FOUND)

    def put(self,request,*args,**kwargs):

        try:
            profile=UserProfile.objects.get(user=request.user)

            serializer=self.serializer_class(profile,data=request.data)

            if serializer.is_valid():
                serialized_data=serializer.save()

                return Response({
                    'message':'Profile successfully updated',
                    'data':self.serializer_class(serialized_data).data
                },status=status.HTTP_200_OK)
            
            else:

                return Response({
                    'message':'Invalid data',
                    'data':{}
                },status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            pass
            

class TransactionsView(APIView):
    serializer_class=UserProfileSerializer
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]

    def get_transaction_type_amount(self,transactions=None, payment_type=None):
        transaction_amount={}
        debit_amount=0
        credit_amount=0

        
        for transaction in transactions:
            if payment_type is not None:
                
                
                if payment_type == 'credit':
                    credit_amount+=float(transaction['amount'])
                    
                else: 
                    debit_amount+=float(transaction['amount'])
            else:
                if transaction['payment_type'] == 'credit':
                    
                    credit_amount+=float(transaction['amount'])
                    
                if transaction['payment_type'] == 'debit':
                    debit_amount+=float(transaction['amount'])

        transaction_amount['credit']=credit_amount
        transaction_amount['debit']=debit_amount
        return transaction_amount


    def get(self,request):
        payment_type=request.GET.get('payment_type',None)

        allObjects=AllObjects(request.user)
        transactions=allObjects['transaction']
        wallet=allObjects['wallet']
    
        for transaction in transactions:

            transaction['user']=UserSerializer(User.objects.get(id=transaction['user']),many=False).data
        
        
        month=request.GET.get('month',datetime.now().month)
        year=request.GET.get('year', datetime.now().year)

        if month and year in [None, '']:
                return Response({'data':transactions,'wallet':wallet},status=status.HTTP_200_OK)
        
        else:
            data=list(filter(lambda x: datetime.fromisoformat(x['created_at'].replace("Z","+00:00")).month == int(month) 
                                and datetime.fromisoformat(x['created_at'].replace("Z","+00:00")).year == int(year),
                                transactions))

            if payment_type in [None, '']:
                amount=self.get_transaction_type_amount(data)

                return Response({'data':data,'amount':amount,'wallet':wallet},status=status.HTTP_200_OK)
            else:     
                
                transactions_type=list(filter(lambda x: x['payment_type'] == payment_type ,data))
                amount=self.get_transaction_type_amount(transactions_type,payment_type)
                          
                return Response({'data':transactions_type,'amount':amount,'wallet':wallet},status=status.HTTP_200_OK)


class BroadCastMailsView(APIView):
    def post(self,request):
        subject=request.data.get('subject')
        message=request.data.get('message')
        mail_type=str(request.data.get('mail_type')).strip()

        if mail_type.upper()== 'INTERNAL':
            emails=request.data.get('emails',None)
            if emails is not None:
                send_user_message(
                    subject,
                    message,
                    '',
                )
                return Response({ 'message':'mail sent successfully' }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'message':'No email attached'
                },status=status.HTTP_406_NOT_ACCEPTABLE)
            
        else:
            pass

@api_view(['GET'])
def APIendpoints(request):

    data = [
            [
            'auth/',
            ['register/', 'activate/account/', 'login/','verify/social/',
             'password/change/', 'password/verify/',
             'kyc/apply/', 'kyc/status/','kyc/approve/<str:id>/','token/refresh/',
             'verify/social/google-oauth2/'
             ]
            ],

             ['virtual-card/',
              ['create/','retrieve/cardholder/','update/cardholder', 'fund/payment/',
               'ephemeral/keys/','payment/webhook/', 'add/naira/','add/dollar/','webhook/',"more/",'authorization/webhook/'],
             ],

           
             [ 'payment/',
              [
                 "paystack-webhook/", 'api/banks-list/','bank/transfer/',
                 'create-bank-accounts/', 'retrieve/user/account-list/',
                  
              ]
              
                 
             ],
             ['profile/','transactions/'],
             ['vtu/',
              [
                  'validate/phone-number/','service/variations/','pay/airtime-data/',
                  'verify/meter/','pay/utility/',
              ]
              ],

            [
                'wallet/',
                [
                    'swap/currencies/'
                ]
            ]
             
              
             ]
    return Response(data)



from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.generics import CreateAPIView,DestroyAPIView
from rest_framework.response import Response
# Create your views here.
from rest_framework.decorators import api_view

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated,AllowAny
from userauth.views import getUserData
from .serializers import *
from rest_framework import status
from payment import models as pmodels
from payment.serializers import DedicatedAccountSerializer
from datetime import datetime


def AllObjects(user):
    objects={}
    try:
        transaction=Transaction.objects.filter(user=user)
        objects['transaction']=TransactionSerializer(transaction,many=True).data
    except:
        objects['transaction']=[]

    try:
        wallet=Wallet.objects.get(user=user)
        objects['wallet']=WalletSerializer(wallet,many=False).data
    except:
        objects['wallet']=[]

    try:
        kyc=KYCVerification.objects.filter(user=user)
        objects['kyc']=KYCVerificationSerializer(kyc,many=False).data
    except:
        objects['kyc']=[]

    
    try:
        dva=pmodels.DedicatedAccount.objects.filter(user=user).first()
        objects['dva']=DedicatedAccountSerializer(dva,many=False).data
    except:
        objects['dva']=[]

    try:
        card=Card.objects.filter(user=user,issued=True).first()
        objects['card']=Cardserializer(card,many=False).data
    except:
        objects['card']=[]

    return objects

class UserProfileDataView(APIView):
    serializer_class=UserProfileSerializer
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    
    def get(self,request,*args,**kwargs):
        try:
            allObjects=AllObjects(request.user)
            profile=UserProfile.objects.get(user=request.user)
            serializer=self.serializer_class(profile,many=False).data


            serializer['user']=UserSerializer(User.objects.get(id=serializer['user']),many=False).data
            serializer['allObjects']=allObjects

            return Response({
                'data':serializer
            },status=status.HTTP_200_OK)

        except Exception as e:
            return Response({
                'message':e,
                'data':{},

            },status=status.HTTP_404_NOT_FOUND)

    def put(self,request,*args,**kwargs):

        try:
            profile=UserProfile.objects.get(user=request.user)

            serializer=self.serializer_class(profile,data=request.data)

            if serializer.is_valid():
                serialized_data=serializer.save()

                return Response({
                    'message':'Profile successfully updated',
                    'data':self.serializer_class(serialized_data).data
                },status=status.HTTP_200_OK)
            
            else:

                return Response({
                    'message':'Invalid data',
                    'data':{}
                },status=status.HTTP_400_BAD_REQUEST)
        except ObjectDoesNotExist:
            pass
            

class TransactionsView(APIView):
    serializer_class=UserProfileSerializer
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]

    def get_transaction_type_amount(self,transactions=None, payment_type=None):
        transaction_amount={}
        debit_amount=0
        credit_amount=0

        
        for transaction in transactions:
            if payment_type is not None:
                
                
                if payment_type == 'credit':
                    credit_amount+=float(transaction['amount'])
                    
                else: 
                    debit_amount+=float(transaction['amount'])
            else:
                if transaction['payment_type'] == 'credit':
                    
                    credit_amount+=float(transaction['amount'])
                    
                if transaction['payment_type'] == 'debit':
                    debit_amount+=float(transaction['amount'])

        transaction_amount['credit']=credit_amount
        transaction_amount['debit']=debit_amount
        return transaction_amount


    def get(self,request):
        payment_type=request.GET.get('payment_type',None)

        allObjects=AllObjects(request.user)
        transactions=allObjects['transaction']
        wallet=allObjects['wallet']
        
        month=request.GET.get('month',datetime.now().month)
        year=request.GET.get('year', datetime.now().year)

        if month and year in [None, '']:
                return Response({'data':transactions,'wallet':wallet},status=status.HTTP_200_OK)
        
        else:
            data=list(filter(lambda x: datetime.fromisoformat(x['created_at'].replace("Z","+00:00")).month == int(month) 
                                and datetime.fromisoformat(x['created_at'].replace("Z","+00:00")).year == int(year),
                                transactions))

            if payment_type in [None, '']:
                amount=self.get_transaction_type_amount(data)

                return Response({'data':data,'amount':amount,'wallet':wallet},status=status.HTTP_200_OK)
            else:     
                
                transactions_type=list(filter(lambda x: x['payment_type'] == payment_type ,data))
                amount=self.get_transaction_type_amount(transactions_type,payment_type)
                          
                return Response({'data':transactions_type,'amount':amount,'wallet':wallet},status=status.HTTP_200_OK)




@api_view(['GET'])
def APIendpoints(request):

    data = [
            [
            'auth/',
            ['register/', 'activate/account/', 'login/','verify/social/',
             'password/change/', 'password/verify/',
             'kyc/apply/', 'kyc/status/','kyc/approve/<str:id>/','token/refresh/',
             'verify/social/google-oauth2/'
             ]
            ],

             ['virtual-card/',
              ['create/','retrieve/cardholder/','update/cardholder', 'fund/payment/',
               'ephemeral/keys/','payment/webhook/', 'add/naira/','add/dollar/','webhook/',"more/",'authorization/webhook/'],
             ],

           
             [ 'payment/',
              [
                 "paystack-webhook/", 'api/banks-list/','bank/transfer/',
                 'create-bank-accounts/', 'retrieve/user/account-list/',
                  
              ]
              
                 
             ],
             ['profile/','transactions/'],
             ['vtu/',
              [
                  'validate/phone-number/','service/variations/','pay/airtime-data/',
                  'verify/meter/','pay/utility/',
              ]
              ],

            [
                'wallet/',
                [
                    'swap/currencies/'
                ]
            ]
             
              
             ]
    return Response(data)


