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

from virtualcard.utils import *
import base64

stripe.api_key=settings.STRIPE_SECRET_KEY



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
            "individual[card_issuing][user_terms_acceptance][ip]":'156.22.55.115',
            "spending_controls[allowed_categories][0]":"general_services",
            "spending_controls[spending_limits][0][amount]":10000,
            "spending_controls[spending_limits][0][interval]":'daily',
            "spending_controls[spending_limits_currency]":'USD',
            "spending_controls[blocked_merchant_countries]":[],
            


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
      



class AddFundToStripeCard(APIView):
   permission_classes=[IsAuthenticated]
   authentication_classes=[JWTAuthentication]

   def get(self,request):
      pass
   def post(self,request):
      res=StripePaymentUtils.get_paysit_stripe_balance()
      return Response(res)

   





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




@csrf_exempt
def card_authorization_webhook(request): #Handles all card authorization events when a purchase is made with the card
    payload = request.body
    event = None
    


    try:
      event = stripe.Event.construct_from(
         json.loads(payload), stripe.api_key
      )
    except ValueError as e:
      # Invalid payload
      return HttpResponse(status=400)
   #  print('AUTHORIZATION ',event)

    # Handle virtual card transaction
    if event['type'] == 'issuing_transaction.created':
       
        transaction = event['data']['object']
        card_id = transaction['card']
        amount = transaction['amount'] / 100  # Stripe uses cents
        currency = transaction['currency']
        print('ID  ',event['data'])

      #   # Find user with this virtual card
      #   try:
      #       profile = UserProfile.objects.get(virtual_card_id=card_id)
            
      #   except UserProfile.DoesNotExist:
      #       pass

    return HttpResponse(status=200)