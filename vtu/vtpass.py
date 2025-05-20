import re
import requests
from django.conf import settings
from datetime import datetime
import string
import random
from .utils import extract_size_name,add_commision,data_percentage_add
import math
from decimal import Decimal
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
        units=['mb','gb','tb']
        for unit in units:
            obj=[i for i, val in enumerate(arr) if unit.upper() in val ]
            if len(obj) > 0:
                return arr[obj[0]]
            
            
        

    def GetServiceVariations(self,service_id):
        url=f'{base_url}service-variations?serviceID={service_id}'
        res=requests.get(url=url,headers=get_req_headers)
        response = res.json()
        plans =[]
        
        for item in response['content']['variations']:
                    new_item={}
                    new_item['price']=Decimal(math.ceil((add_commision(item['variation_amount']))))
                    new_item['provider_price'] = float(item['variation_amount'])#normal_amount
                    new_item['plan_id']=str(item['variation_code']).strip()
                    new_item['provider']='VTPASS'
                    new_item['service_id'] =service_id
                    new_item['name']=item['name']
                    new_item['network']=str(service_id).upper().split('-')[0]
                    
                    if 'data'  in str(service_id).strip():
                        duration,qty = extract_size_name(item['name'])
                        new_item['duration'] =duration
                        new_item['qty'] =qty
                    else:
                        new_item['name']=str(item['variation_code']).replace('-',' ').capitalize()
                        new_item['network']=str(service_id).upper()
                        
                    plans.append(new_item)


        return plans
    


    def PayForAirtimeService(self,data):
         
        # request_id=generate_vtu_request_id(10)
        
        payload={
            'request_id':data['request_id'],
            'serviceID':data['service_id'],
            'amount':data['amount'],
            'phone':str(data['phone_no'])

        }
        
        
        
        try:
            res=requests.post(url=self.url,headers=post_req_headers,data=payload)
            res =res.json()
           
            status ='success'
            if res['content']['transactions']['status'] == 'delivered':
                status ="completed"
            elif res['content']['transactions']['status'] == 'pending':
                status='pending'
            elif res['content']['transactions']['status'] == 'failed':
                status='failed'
        
            else:
                status = "failed"

            return status
        except Exception as e:
            return "failed"

    def verify_transaction_status(self,request_id):
        
        payload={
            'request_id':request_id,
        }
        print('in vtpass ',payload)
        try:
            res=requests.post(url=f'{base_url}requery',headers=post_req_headers,data=payload)
            print(res.json())

            response =res.json()
            
            if response['content']['transactions']['status'] == 'delivered':
                return 'completed'
            elif response['content']['transactions']['status'] == "pending":
                return 'pending'
            else:
                return 'failed'
            
        except Exception as e:
            print(f"VTPass verification error: {e}")
            return "pending"
            

        


    def PayForDataService(self,data): 
        print(data)      
        payload={
            'request_id':data['request_id'],
            'serviceID':data['service_id'],
            'billersCode':str(data['phone_no']),
            'phone':str(data['phone_no']),
            'variation_code':data['plan_id'],
            'amount': float(data['price'])/float(1+(data_percentage_add/100))
        }
        try:
            res=requests.post(url=self.url,headers=post_req_headers,data=payload)
            res =res.json()
            print(res)
            status ='success'
            if res['content']['transactions']['status'] == 'delivered':
                status ="completed"
            elif res['content']['transactions']['status'] == 'pending':
                status='pending'
            elif res['content']['transactions']['status'] == 'failed':
                status='failed'
        
            else:
                status = "failed"

            return status
        except Exception as e:
            return False
    




    def VerifyMeterNumber(self,billers_code,service_id,service_type='prepaid'):
        url=f'{base_url}merchant-verify'
        payload={
            'billersCode':int(billers_code),
            'serviceID':service_id,
            'type':service_type
        }
        res=requests.post(url=url,headers=post_req_headers,data=payload)

        return res.json()
    



    
    def PayForElectricityService(self,data):

        # request_id=generate_vtu_request_id(10)
        
        payload={
            'request_id':data['request_id'],
            'serviceID':data['service_id'],
            'billersCode':str(data['billers_code']),
            'phone':str(data['phone_no']),
            'variation_code':data['meter_no'],
            'amount':data['amount']

        }
        res=requests.post(url=self.url,headers=post_req_headers,data=payload)
        data=res.json() 

        try:

            status=None
            if data['content']['transactions']['status'] =='delivered':
                status='completed'
            elif data['content']['transactions']['status']=='pending':
                status='pending'
            elif data['content']['transactions']['status']=='failed':
                status='failed'
                
            return data,status
        except Exception as e:
            return False
    

    def VerifySmartCardNumber(self,card_number,service_id):
        url='https://sandbox.vtpass.com/api/merchant-verify'
        
        payload={
            'billersCode':card_number,
            'serviceID':service_id
        }


        res=requests.post(url=url,headers=post_req_headers,data=payload)
        return res.json()
    
    def PayForTvService(self,data):
       
        payload={
            'request_id':data['request_id'],
            'serviceID':data['service_id'],
            'billersCode':str(data['card_no']),
            'amount':float(data['price'])/float(1+(data_percentage_add/100)),
            'phone':str(data['phone_no']),
            'subscription_type':data['subscription_type']

        }
        if data['subscription_type'] == 'change':
            payload['variation_code']=data['plan_id']

        print(payload)

        res=requests.post(url=self.url,headers=post_req_headers,data=payload)

        data=res.json() 
        print(data)
        try:

            status=None
            if data['content']['transactions']['status'] =='delivered':
                status='completed'
            elif data['content']['transactions']['status']=='pending':
                status='pending'
            elif data['content']['transactions']['status']=='failed':
                status='failed'
                
            return data,status
        except Exception as e:
            return False

       
    


