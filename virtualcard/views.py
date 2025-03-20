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

stripe.api_key=settings.STRIPE_SECRET_KEY



def get_user_ip(request):
    ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
    if ip_address:
        ip_address = ip_address.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    return ip_address


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
            "individual[card_issuing][user_terms_acceptance][ip]":ip_addr


        }
            
            if card.issued == True:
               return Response({
                  'message':'Card already issued to user',
                  'data':Cardserializer(card).data,
                  'status':'ok',
               })
            


            else:

              res=StripePaymentUtils.create_card_holder(data=data)
  
              return Response({
                  'status':'ok',
                  'data':res,
                  'message':'card successfully issued'
                  

                })

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
            })
         else:
            return Response({
               'data':{},
               'message':'User card is not issued'
            })
      except ObjectDoesNotExist:
         return Response({
            'data':{},
            'message':'No card data found'
         }) 
      


      
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
            })
         else:
            return Response({
               'data':{},
               'message':'User card is not issued'
            })
      except ObjectDoesNotExist:
         return Response({
            'data':{},
            'message':'No card data found'
         }) 

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
   permission_classes=[IsAuthenticated]
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

  
#   print(payload)
  try:
    event = stripe.Event.construct_from(json.loads(payload), settings.STRIPE_SECRET_KEY)
  except ValueError as e:
    # Invalid payload
    return HttpResponse(status=400)

  # Handle the event

  data={
        'id':event['data']['object']['id'],
        
        }
  print(event.type)
  
  user_email=event['data']['object']['email']
  print(user_email)

  
  if event.type == 'issuing_cardholder.created':
    
    StripePaymentUtils.create_card(data=data,email=user_email)
#   elif event.type == 'issuing_cardholder.updated':
#     StripePaymentUtils.update_card(data=data) 
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
   print(event)
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