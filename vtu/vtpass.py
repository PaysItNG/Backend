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
            'public-key':settings.VTPASS_TEST_PUB,
            'Content-Type': 'application/json'
        }

post_req_headers={
            'Content-Type': 'application/json',
            'api-key':settings.VTPASS_TEST_APIKEY,
            'secret-key':settings.VTPASS_TEST_SECRET
        }






providers ={ #create a service mapper
            "mtn":"your_desired_service_id ",
            "airtel":"",
            "glo":"",
            "etisalat": ""
        }
class VtuServicesUtils():
    

    def GetServiceVariations(service_id):
        
        service_id = providers[service_id] # use it this way
        
        url=f'{base_url}service-variations?serviceID={service_id}'
        

        res=requests.get(url=url,headers=get_req_headers)

        # print(res.json())

        return res.json()
    
    def PayForAirtimeService(service_id,amount,phone_no):
         
        request_id=generate_vtu_request_id(10)
        
        payload={
            'request_id':request_id,
            'serviceID':service_id,
            'amount':amount,
            'phone':phone_no

        }
        url=f'{base_url}pay'
        res=requests.post(url=url,headers=post_req_headers,data=payload)

        # print(res.json())
        return res.json()


    def PayForDataService(service_id,phone_no,variation_code):
         
        request_id=generate_vtu_request_id(10)
        
        payload={
            'request_id':request_id,
            'serviceID':service_id,
            'billersCode':phone_no,
            'phone':int(phone_no),
            'variation_code':variation_code

        }
        url=f'{base_url}pay'
        res=requests.post(url=url,headers=post_req_headers,data=payload)

        return res.json()
    


    def VerifyMeterNumber(billers_code,service_id,service_type='prepaid'):
        url=f'{base_url}merchant-verify'
        payload={
            'billersCode':int(billers_code),
            'serviceID':service_id,
            'type':service_type
        }
        res=requests.post(url=url,headers=post_req_headers,data=payload)

        return res.json()
    

    
    def PayForElectricityService(billers_code,service_id,phone_no,amount,variation_code='prepaid'):

        request_id=generate_vtu_request_id(10)
        url=f'{base_url}pay'
        
        payload={
            'request_id':request_id,
            'serviceID':service_id,
            'billersCode':int(billers_code),
            'phone':int(phone_no),
            'variation_code':variation_code,
            'amount':amount

        }
        res=requests.post(url=url,headers=post_req_headers,data=payload)
        return res.json()