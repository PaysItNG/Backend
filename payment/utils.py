
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.response import Response
import requests,json
from .models import DedicatedAccount

PSTACK_PUBLIC_KEY=settings.PSTACK_PUBLIC_KEY
PSTACK_SECRET_KEY=settings.PSTACK_SECRET_KEY
User = get_user_model()

class PayStackUtils:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {PSTACK_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        self.base_url ='https://api.paystack.co'

    def create_paystack_customer(self,email,first_name,last_name,phone_number):#Create a customer 
        #Every transaction or virtual account must be linked to a customer in Paystack.
        #When a user signs up, automatically create a Paystack customer for them

        payload = {"email":email,"first_name":first_name,"last_name":last_name,"phone":phone_number}
         # Debugging: Print the response content before calling .json()

        response=requests.post(f"{self.base_url}/customer",
                               proxies={"http": None, "https": None},
                               json=payload,headers=self.headers)
        print("Paystack Response Status:", response.status_code)
        #print("Paystack Response Text:", response.text)
        if response.status_code != 200:  
             return {'error': response.json().get("message", "An error occurred.")}, response.status_code  
        return response.json()
    
    def create_virtual_account(self,customer_code, preferred_bank="wema-bank"):
        """
        Create a dedicated virtual account (NUBAN) for an existing Paystack customer.
        """
        payload = {
            "customer": customer_code,
            "preferred_bank": preferred_bank
        }
        response = requests.post(f"{self.base_url}/dedicated_account", 
                                 proxies={"http": None, "https": None},
                                 headers=self.headers, json=payload)
        
        if response.status_code != 200:  
            return {'error': response.json().get("message", "An error occurred.")}, response.status_code  
        return response.json()
    def create_customer_and_virtual_account(self,email,first_name,last_name,phone, preferred_bank="wema-bank"):
        """
        Create a dedicated virtual account (NUBAN) for an existing Paystack customer.
        """
        payload = {
        "email":email,
        "first_name":first_name,
        "last_name":last_name,
        "phone": phone,
        "preferred_bank":preferred_bank,
        "country": "NG"
        }
        user = User.objects.get(email=email)
        response = requests.post(f"{self.base_url}/dedicated_account", 
                                 proxies={"http": None, "https": None},
                                 headers=self.headers, json=payload)
        
        if response.status_code != 200:  
            #return {'error': response.json().get("message", "An error occurred.")}, response.status_code  
            return False
        data = response.json()
        DedicatedAccount.objects.create(user=user,
                                     bank_name= data['data']['bank'],
                                     account_number=data['data']['account_number'],
                                     account_name =data['data']['account_name']
                                     )
        return True
    
    def paystack_payment(self,email,data):
        payload = {
            "email": email,
            "amount": int(data['amount']) * 100,  # Amount in kobo
            
        }
        response = requests.post(f'{self.base_url}/transaction/initialize', headers=self.headers, json=payload)

        if response.status_code != 200:  
            return {'error': response.json().get("message", "An error occurred.")}, response.status_code  
        return response.json()

    
    def verify_transaction(self,reference):
        """
        Verify a transaction on Paystack using the transaction reference.
        """
        response = requests.get(f"{self.base_url}/transaction/verify/{reference}", headers=self.headers)
        if response.status_code != 200:  
            return {'error': response.json().get("message", "An error occurred.")}, response.status_code  
        return response.json()
    
    def create_transfer_recipient(self,name, account_number, bank_code, currency="NGN"):
        """Creates a transfer recipient and returns the recipient code."""
        url = f"{self.base_url}/transferrecipient"
 
        payload = {
        "type": "nuban", "name": name, "account_number": account_number, "bank_code": bank_code,"currency": currency,
            }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code != 200:  
            return {'error': response.json().get("message", "An error occurred.")}, response.status_code  
        return response.json()
    
    def get_transfer_recipient(self,recipient_code):
        """Fetch transfer recipient details from Paystack"""
        url = f"{self.base_url}/transferrecipient/{recipient_code}"
        response = requests.get(url, headers=self.headers)
        if response.status_code != 200:  
                return {'error': response.json().get("message", "An error occurred.")}, response.status_code  
        return response.json()
    
    def transfer(self,amount, recipient_code, reason="Transfer from PaysIt"):
        """
        Transfers money to a customer using Paystack.
        """
        payload = {
        "source": "balance", "reason": reason,
            "amount": int(amount * 100),  # Convert Naira to kobo
            "recipient": recipient_code,
        }
        response = requests.post(f"{self.base_url}/transfer", headers=self.headers, json=payload)
        if response.status_code != 200:  
            return {'error': response.json().get("message", "An error occurred.")}, response.status_code  
        return response.json()

    def get_bank_list(self):
        """Retrieve a list of banks from Paystack."""  
        try:  
            response = requests.get(f"{self.base_url}/bank", headers=self.headers)  
            if response.status_code == 200:  
                banks = response.json().get('data', [])  
                return banks  # Return raw bank data  
            return {'error': 'Unable to fetch banks, please try again later.'}, response.status_code  
        except requests.exceptions.RequestException as e:  
            return {'error': str(e)}, 500  