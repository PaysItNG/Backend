import re
import requests
from django.conf import settings
from datetime import datetime
import string
import random

def generate_vtu_request_id(length):
    char=string.ascii_lowercase+string.digits
    random_id="".join(random.choice(char) for _ in range(length))
    now=str(datetime.now())
    val=''
    for char in now:
        if char in ['-',' ']:
            continue
        else:
            val += char

    token=val.split(':')[0]+val.split(':')[1]
    request_id=token+random_id
    return request_id

def validate_phonenumber(number):
    network_provider=''
    number_valid=False
    if re.match(r'^(?:\+234|0)?(803|806|703|706|810|813|814|816|903|906|913|916)\d{7}$',number):
        network_provider = 'mtn'
        number_valid=True
    elif re.match(r'^(?:\+234|0)?(809|817|818|908|909)\d{7}$',number):

        network_provider = 'etisalat'
        number_valid=True
    
    elif re.match(r'^(?:\+234|0)?(701|708|802|808|812|901|902|904|907|912|911)\d{7}$',number):
        network_provider = 'airtel'
        number_valid=True
    elif re.match(r'^(?:\+234|0)?(705|805|807|811|815|905)\d{7}$',number):
        network_provider = 'glo'
        number_valid=True
    

    return network_provider,number_valid


# VTU SERVICES
base_url='https://sandbox.vtpass.com/api/'
get_req_headers={
            'api-key':settings.VTPASS_TEST_APIKEY,
            'public-key':settings.VTPASS_TEST_PUB
        }

post_req_headers={
            'api-key':settings.VTPASS_TEST_APIKEY,
            'secret-key':settings.VTPASS_TEST_SECRET
        }








class VtuServicesUtils():


    def __init__(self):
        self.url=f'{base_url}pay'

    def extractDataSize(self,arr):
        # print(arr)
        units=['mb','gb']
        for unit in units:
            obj=[i for i, val in enumerate(arr) if unit.upper() in val ]
            if len(obj) > 0:
                return arr[obj[0]]
            
            
        

    def GetServiceVariations(self,service_id):
        url=f'{base_url}service-variations?serviceID={service_id}'
        res=requests.get(url=url,headers=get_req_headers)

        return res.json()
    


    def PayForAirtimeService(self,service_id,amount,phone_no):
         
        request_id=generate_vtu_request_id(10)
        
        payload={
            'request_id':request_id,
            'serviceID':service_id,
            'amount':amount,
            'phone':phone_no

        }
        
        res=requests.post(url=self.url,headers=post_req_headers,data=payload)

        # print(res.json())
        return res.json()




    def PayForDataService(self,service_id,phone_no,variation_code,amount):
         
        request_id=generate_vtu_request_id(10)
        
        payload={
            'request_id':request_id,
            'serviceID':service_id,
            'billersCode':phone_no,
            'phone':int(phone_no),
            'variation_code':variation_code,
            'amount':float(amount)/1.5

        }
        
        res=requests.post(url=self.url,headers=post_req_headers,data=payload)

        return res.json()
    




    def VerifyMeterNumber(self,billers_code,service_id,service_type='prepaid'):
        url=f'{base_url}merchant-verify'
        payload={
            'billersCode':int(billers_code),
            'serviceID':service_id,
            'type':service_type
        }
        res=requests.post(url=url,headers=post_req_headers,data=payload)

        return res.json()
    



    
    def PayForElectricityService(self,billers_code,service_id,phone_no,amount,variation_code='prepaid'):

        request_id=generate_vtu_request_id(10)
        
        payload={
            'request_id':request_id,
            'serviceID':service_id,
            'billersCode':int(billers_code),
            'phone':int(phone_no),
            'variation_code':variation_code,
            'amount':amount

        }
        res=requests.post(url=self.url,headers=post_req_headers,data=payload)
        return res.json()
    

    def VerifySmartCardNumber(self,card_number,service_id):
        url='https://sandbox.vtpass.com/api/merchant-verify'
        
        payload={
            'billersCode':card_number,
            'serviceID':service_id
        }


        res=requests.post(url=url,headers=post_req_headers,data=payload)
        return res.json()
    
    def PayForTvService(self):
        request_id=generate_vtu_request_id(10)
        url=f'{self.url}pay'
    


