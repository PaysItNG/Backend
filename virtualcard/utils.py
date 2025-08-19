import stripe
from django.conf import settings
from main.models import  *
stripe.api_key=settings.STRIPE_SECRET_KEY
api_key=settings.STRIPE_SECRET_KEY
import requests
import datetime
from decimal import Decimal


base_url='https://api.stripe.com'

headers={
        "Authorization": f"Bearer {api_key}"

    }
class StripePaymentUtils():



    def get_paysit_stripe_balance():
        res=stripe.Balance.retrieve()
        return res
    

    @staticmethod
    def create_card_holder(data)->dict:
        """
            create a  cardholder instance      
        """

        url=f'{base_url}/v1/issuing/cardholders'
        res=requests.post(url,headers=headers,data=data)
       
        return res.json()

    @staticmethod
    def update_card_holder(data)->dict:
        res=stripe.issuing.Cardholder.modify(
            data.card_holder_ref_id,
            spending_controls={
               
                'spending_limits':[
                    {
                        'amount':100000,
                        'interval':'daily',

                    }
                ],
                'allowed_categories':['general_services','advertising_services']
            },
            metadata={"order_id": "6735"},
            )
        
        return res


    @staticmethod
    def retrieve_card_holder(data)->dict:
        url=f"{base_url}/v1/issuing/cardholders/{data.card_holder_ref_id}"
        res=requests.get(url=url,headers=headers)

        return res.json()

    

    @staticmethod
    def create_card(data,email,VIRTUAL_CARD_PRICE_USD):
        """
            create a virtual card for user and assign as cardholder       
        """

        url=f"{base_url}/v1/issuing/cards"
        card,_=Card.objects.get_or_create(user__email=email)
        wallet=Wallet.objects.get(user__email=email)
       
        
        res=stripe.issuing.Card.create(
            cardholder=data['id'],
            currency='usd',
            status='active',
            type='virtual',
            spending_controls={
                'spending_limits':[
                    {
                        'amount':100000,
                        'interval':'daily',
 
                    }
                ],
                'allowed_categories':data['spending_controls']['allowed_categories']
            }
        )
        response=res

        
        card.card_holder_ref_id=str(data['id']).strip()
        card.card_ref_id=str(response['id']).strip()
        card.expiry_date=datetime.datetime(response['exp_year'],response['exp_month'],1)
        card.user=User.objects.get(email=email)
        card.card_holder_name=response['cardholder']['name']
        card.issued=True
        card.card_type=response['type']
        card.card_brand=response['brand']
        card.last_four=response['last4']
        card.status=response['status']
       
      
        # Deduct price from wallet (if that’s the intended behavior)
        wallet.usd_balance = Decimal(wallet.usd_balance) - VIRTUAL_CARD_PRICE_USD
        wallet.save(update_fields=["usd_balance"])
        
        card.save()
       
        return response
    
    @staticmethod
    def update_card(data,email):
        card,_=Card.objects.get_or_create(user__email=email)
        print(data)
        res=stripe.issuing.Card.modify(
        card.card_ref_id,
        metadata={"order_id": "6735"},
         spending_controls={
                
                'spending_limits':[
                    {
                        'amount':100000,
                        'interval':'daily',
 
                    }
                ],
                'allowed_categories':data['spending_controls']['allowed_categories']
            
            },
        
        )

        print(res)
        return res

    @staticmethod
    def create_payment_intent(data):
        url=f"{base_url}/v1/payment_intents"
        # res=requests.post(url=url,headers=headers,data=data)
        res = stripe.PaymentIntent.create(
            amount=data['amount'],
            currency=data['currency'],
            payment_method_types=["card"],  # Correct (array)
        )

        return res
    

    #to be refactored
    def confirm_payment_intent(data):
        res=stripe.PaymentIntent.confirm(
                    "pi_3MtweELkdIwHu7ix0Dt0gF2H", #PAYMENT INTENT ID
                    payment_method="pm_card_visa",
                    return_url=" ",
                    )

        return res
    


    def update_card_authorization(data):
        res=stripe.issuing.Authorization.modify(
            "iauth_1JVXl82eZvKYlo2CPIiWlzrn",
            metadata={"order_id": "6735"},
            )
        
        return res
    
    def approve_authorization(data):
        res=stripe.issuing.Authorization.approve(
            data['id']
        )

        return res

    def exchange_conversion(from_curr,to_curr,amount):
        url='https://api.currencylayer.com/convert'
        params={
            'access_key':'3263fca29bbc7eae94c823b8ee2cb213',
            'from':from_curr,
            'to':to_curr,
            'amount':amount

        }
        res=requests.get(url=url,params=params)

        return res.json()

