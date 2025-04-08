from django.shortcuts import render

# Create your views here

import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
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
import string
import random
from django.utils import timezone
import stripe
from rest_framework.decorators import api_view
from virtualcard.utils import *
import base64
from django.views import View
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from decimal import Decimal

stripe.api_key=settings.STRIPE_SECRET_KEY

webhook_secret=settings.STRIPE_WEBHHOOK_SECRET

def get_user_ip(request):
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_address:
        ip_address = ip_address.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    return ip_address



# base_url='https://sandbox-api.marqeta.com/v3/'




class CreateVirtualCardView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
  
    def post(self,request,*args,**kwargs):
            ip_addr=get_user_ip(request=request)
            card,created=Card.objects.get_or_create(user=request.user)

 
            data = {
            "type": "individual",
            "name": f"{request.user.first_name} {request.user.last_name}",
            "email": f"{request.user.email}",
            "phone_number": "+18888675322",
            "billing[address][line1]": "1234 Main Street",
            "billing[address][city]": "San Francisco",
            "billing[address][state]": "CA",
            "billing[address][country]": "US",
            "billing[address][postal_code]": "94111",
            "individual[first_name]":request.user.first_name,
            "individual[last_name]":request.user.last_name,
            "individual[card_issuing][user_terms_acceptance][date]":int(timezone.now().timestamp()),
            "individual[card_issuing][user_terms_acceptance][ip]":get_user_ip(request=request),
            "spending_controls[allowed_categories]" :None,
            "spending_controls[spending_limits][0][amount]":100000,
            "spending_controls[spending_limits][0][interval]":'daily',
            "spending_controls[spending_limits_currency]":'USD',
            "spending_controls[blocked_merchant_countries][0]":[],
            "spending_controls[allowed_categories][0]":['general_services'],
             "spending_controls[allowed_categories][1]":['advertising_services'],
            


        }
            
            if card.issued == True:
               return Response({'message':'Card already issued to user','data':Cardserializer(card).data,},status=status.HTTP_200_OK)
            
            else:

              res=StripePaymentUtils.create_card_holder(data=data)
  
              return Response({
                  'data':res,
                  'message':'card successfully issued'
                  

                },status=status.HTTP_201_CREATED)




class UpdateCardholderView(APIView):
   permission_classes=[IsAuthenticated]
   authentication_classes=[JWTAuthentication]
   def post(self,request,*args,**kwargs):
      try:
         card=Card.objects.get(user=request.user)
         if card.issued == True:
            res=StripePaymentUtils.update_card_holder(card)
            return Response({
               'data':res,
               'message':'User card updated'
            },status=status.HTTP_201_CREATED)
         else:
            return Response({
               'data':{},
               'message':'User card is not issued'
            },status=status.HTTP_400_BAD_REQUEST)
      except ObjectDoesNotExist:
         return Response({
            'data':{},
            'message':'No card data found'
         },status=status.HTTP_404_NOT_FOUND) 
      


      
class CardHolderRetrieveView(APIView):
   permission_classes=[IsAuthenticated]
   authentication_classes=[JWTAuthentication]
   def get(self,request,*args,**kwargs):
      try:
         card=Card.objects.get(user=request.user)
         if card.issued == True:
            res=StripePaymentUtils.retrieve_card_holder(card)
            return Response({
               'data':res,
               'message':'User card retieved'
            },status=status.HTTP_200_OK)
         else:
            return Response({
               'data':{},
               'message':'User card is not issued'
            },status=status.HTTP_404_NOT_FOUND)
      except ObjectDoesNotExist:
         return Response({
            'data':{},
            'message':'No card data found'
         },status=status.HTTP_404_NOT_FOUND) 
      



class AddFundToDollarCard(APIView):
   permission_classes=[IsAuthenticated]
   authentication_classes=[JWTAuthentication]

   def get(self,request):
      from_currency=str(request.data.get('from_currency')).strip()
      to_currency=str(request.data.get('to_currency')).strip()
      amount=Decimal(request.data.get('amount'))

      currency=StripePaymentUtils.exchange_conversion(to_curr=to_currency,
                                                      from_curr=from_currency,
                                                      amount=amount)
      
      if currency['success'] == True:
         return Response({
            'amount':f"{currency['result']:.2f}",'data':currency['query'],
            'meta_data':currency
         },status=status.HTTP_200_OK)
      
      else:
         return Response({
            'data':{}
         },status=status.HTTP_403_FORBIDDEN)
      

   def post(self,request):
      from_currency=str(request.data.get('from_currency')).strip()
      to_currency=str(request.data.get('to_currency')).strip()
      amount=round(Decimal(request.data.get('amount')),2)
      converted_amount=round(Decimal(request.data.get('converted_amount')),2)
      res=StripePaymentUtils.get_paysit_stripe_balance()
      issuing_balance=res['issuing']['available'][0].to_dict()
      
      if converted_amount < round(issuing_balance['amount']/100,2):
         card,_=Card.objects.get_or_create(user=request.user)

         if card.issued:
            if amount <= Wallet.objects.get(user=request.user).balance:
               card.balance+=converted_amount
               card.save()
               return Response({'message':'Card successfully funded','data':Cardserializer(card).data,
                                'success':True}, status=status.HTTP_200_OK)
            else:
               return Response({'message':'Insuffient funds','data':Cardserializer(card).data,
                                'success':False}, status=status.HTTP_406_NOT_ACCEPTABLE)
         else:
            
            return Response({'message':'Card is not issued,contact support','data':Cardserializer(card).data,
                                'success':False}, status=status.HTTP_406_NOT_ACCEPTABLE)
         

      return Response({'message':'Can\'t fund account at this time, contact support for futher assistance','data':Cardserializer(card).data,
                                'success':False}, status=status.HTTP_406_NOT_ACCEPTABLE)
      


 
   





class PaymentWithStripeView(APIView):
   def post(self,request,*args,**kwargs):
      amount=request.data.get('amount')
      currency=request.data.get('currency')

     

      data={
         'amount':amount,
         'currency':currency,
         "automatic_payment_methods[enabled]":False,
         "payment_method_types": ["card"],
       

      }
      res=StripePaymentUtils.create_payment_intent(data=data)

      return Response(res)




class GenerateEphemeralKeys(APIView):
   permission_classes=[AllowAny]
   authentication_classes=[JWTAuthentication]

   def get(self,request,*args,**kwargs):
      try:
        card=Card.objects.get(user=request.user)
        return Response({
          'secret_key':settings.STRIPE_SECRET_KEY,
          'public_key':settings.STRIPE_PUB_KEY,
          'exists':True,
          'card_id':card.card_ref_id,
          'card_holder_id':card.card_holder_ref_id
        })
      except ObjectDoesNotExist:
         return Response({
            'data':{},
            'exists':False
         })
    
   def post(self,request,*args,**kwargs):
      
      try:
        ephemeralKey = stripe.EphemeralKey.create( nonce=request.data.get('nonce'),
                                        issuing_card=request.data.get('card_id'),
                                        stripe_version='2025-02-24.acacia',
                                    )
        
        return Response({
          'data':ephemeralKey.secret,
          'status':'ok'
        })
      except Exception as e:
         return Response({
          'data':str(e),
          'status':status.HTTP_400_BAD_REQUEST
        })




@csrf_exempt
def virtualcard_webhook_view(request):
  payload = request.body
  event = None

  try:
    event = stripe.Event.construct_from(json.loads(payload), settings.STRIPE_SECRET_KEY)
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)

  # Handle the event

  data={
        'id':event['data']['object']['id'],
        'spending_controls':event['data']['object']['spending_controls']
        
        }
#   print()
  
  user_email=event['data']['object']['email']
#   print(user_email)

  
  if event.type == 'issuing_cardholder.created':
    
    StripePaymentUtils.create_card(data=data,email=user_email)

  if event.type == 'issuing_cardholder.updated':
     StripePaymentUtils.update_card(data=data,email=user_email)

  else:
    print('Unhandled event type {}'.format(event.type))

  return HttpResponse(status=200)




@csrf_exempt
def payment_webhook_view(request):
   payload = request.body
   event = None

   try:
      event = stripe.Event.construct_from(
         json.loads(payload), stripe.api_key
      )
   except ValueError as e:
      # Invalid payload
      return HttpResponse(status=400)

   # Handle the event
   # print(event)
   if event.type == 'payment_intent.succeeded':
      payment_intent = event.data.object # contains a stripe.PaymentIntent
      # Then define and call a method to handle the successful payment intent.
      # handle_payment_intent_succeeded(payment_intent)
   elif event.type == 'payment_method.attached':
      payment_method = event.data.object # contains a stripe.PaymentMethod
      # Then define and call a method to handle the successful attachment of a PaymentMethod.
      # handle_payment_method_attached(payment_method)
   # ... handle other event types
   else:
      print('Unhandled event type {}'.format(event.type))

   return HttpResponse(status=200)



@method_decorator(csrf_exempt, name='dispatch')
class CardAuthorizationWebhook(View): #Handles all card authorization events when a purchase is made with the card

   
   def post(self,request,*args,**kwargs):
      payload = request.body
      signature = request.headers.get("Stripe-Signature")

      try:
         event = stripe.Webhook.construct_event(payload=request.body, sig_header=signature, secret=webhook_secret)
      except ValueError as e:
      # Invalid payload
         return HttpResponse(status=400)

      except stripe.error.SignatureVerificationError as e:
      # Invalid signature
         return HttpResponse(status=400)

      print('AUTHORIZATION ',event['data'])

      # Handle virtual card transaction
      if event['type'] == 'issuing_authorization.request':
         auth = event['data']['object']
         card_id = auth['card']['id']
         amount = auth['pending_request']['amount'] / 100  # Stripe uses cents
         currency = str(auth['currency']).lower()
         print('ID inside request ',auth['pending_request'])

         card=Card.objects.get(card_ref_id=card_id)
         response_data={}

         if amount <= card.balance:
            response_data = {"approved": True}
            card.balance=card.balance-Decimal(amount)
            if currency =='usd':
               card.currency = 'usd'
            elif currency in ['eur','euro']:
               card.currency = 'eur'
            else:
               pass

            card.save()
            # print('success')
         else:
            response_data = {"approved": False}
            print('failed')
         response = JsonResponse(response_data, status=200)
         response["Stripe-Version"] = "2022-08-01"
         return response
      

      return HttpResponse(status=200)
