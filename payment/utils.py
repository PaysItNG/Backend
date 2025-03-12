
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.response import Response
import requests,json
PSTACK_PUBLIC_KEY=settings.PSTACK_PUBLIC_KEY
PSTACK_SECRET_KEY=settings.PSTACK_SECRET_KEY
base_url ='https://api.paystack.co'
User = get_user_model()

class PayStackUtils:

    @staticmethod
    def create_paystack_customer(email,first_name,last_name,phone_number):#Create a customer 
        #Every transaction or virtual account must be linked to a customer in Paystack.
        #When a user signs up, automatically create a Paystack customer for them

        headers = {"Authorization": f'Bearer {PSTACK_SECRET_KEY}'}
        payload = {"email":email,"first_name":first_name,"last_name":last_name,"phone":phone_number}

        response=requests.post(f"{base_url}/customer",data=json.dumps(payload),headers=headers)
        return Response(response.json())
    
    @staticmethod
    def paystack_payment(email,data):
        
        headers = {
            "Authorization": f"Bearer {PSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "email": email,
            "amount": int(data['amount']) * 100,  # Amount in kobo
            
        }

        response = requests.post(f'{base_url}/transaction/initialize', headers=headers, json=payload)


        return Response(response.json())
    
    @staticmethod
    def create_virtual_account(customer_code, preferred_bank="wema-bank"):
        """
        Create a dedicated virtual account (NUBAN) for an existing Paystack customer.
        """
        headers = {
            "Authorization": f"Bearer {PSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        payload = {
            "customer": customer_code,
            "preferred_bank": preferred_bank
        }

        response = requests.post(f"{base_url}/dedicated_account", headers=headers, json=payload)
        
        return Response(response.json())
    @staticmethod
    def verify_transaction(reference):
        """
        Verify a transaction on Paystack using the transaction reference.
        """
        headers = {
            "Authorization": f"Bearer {PSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }

        response = requests.get(f"{base_url}/transaction/verify/{reference}", headers=headers)

        return response.json()
    
    @staticmethod
    def create_transfer_recipient(name, account_number, bank_code, currency="NGN"):
        """Creates a transfer recipient and returns the recipient code."""
        url = f"{base_url}/transferrecipient"
        headers = {
            "Authorization": f"Bearer {PSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
        "type": "nuban", "name": name, "account_number": account_number, "bank_code": bank_code,"currency": currency,
            }
        response = requests.post(url, headers=headers, json=payload)
        return response.json()
    
    @staticmethod
    def get_transfer_recipient(recipient_code):
        """Fetch transfer recipient details from Paystack"""
        url = f"{base_url}/transferrecipient/{recipient_code}"
        headers = {"Authorization": f"Bearer {PSTACK_SECRET_KEY}"}
        response = requests.get(url, headers=headers)
        return response.json()
    
    @staticmethod
    def transfer(amount, recipient_code, reason="Transfer from PaysIt"):
        """
        Transfers money to a customer using Paystack.
        """
        headers = {
            "Authorization": f"Bearer {PSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
        "source": "balance", "reason": reason,
            "amount": int(amount * 100),  # Convert Naira to kobo
            "recipient": recipient_code,
        }
        response = requests.post(f"{base_url}/transfer", headers=headers, json=payload)
        return response.json()
