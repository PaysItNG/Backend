import stripe
from django.conf import settings
from main.models import  *
stripe.api_key=settings.STRIPE_SECRET_KEY
api_key=settings.STRIPE_SECRET_KEY
import requests
import datetime


base_url='https://api.stripe.com'

headers={
        "Authorization": f"Bearer {api_key}"

    }
class StripePaymentUtils():
    
    
    

    @staticmethod
    def create_card_holder(data)->dict:

        url=f'{base_url}/v1/issuing/cardholders'
        res=requests.post(url,headers=headers,data=data)
        # print(res.json())

        return res.json()

    @staticmethod
    def update_card_holder(data)->dict:
        stripe.issuing.Cardholder.modify(
            data.card_holder_ref_id,
            metadata={"order_id": "6735"},
            )


    @staticmethod
    def retrieve_card_holder(data)->dict:
        url=f"{base_url}/v1/issuing/cardholders/{data.card_holder_ref_id}"
        res=requests.get(url=url,headers=headers)

        return res.json()

    

    @staticmethod
    def create_card(data,email):
        

        url=f"{base_url}/v1/issuing/cards"
        card,created=Card.objects.get_or_create(user__email=email)


        card_data={}
        card_data['cardholder']=data['id']
        card_data['currency']='usd'
        card_data['status']='active'
        card_data['type']='virtual'
     
        res=requests.post(url=url,headers=headers,data=card_data)
        # print('Card ',res.json())
        response=res.json()
        
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
        
        card.save()
       
        return response
    
    @staticmethod
    def update_card(data):
        stripe.issuing.Card.modify(
        data['id'],
        metadata={"order_id": "6735"},
        )
