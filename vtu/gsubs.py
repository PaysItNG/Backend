import requests
import asyncio
import aiohttp
from asgiref.sync import async_to_sync
import asyncio
import math
from .vtpass import VtuServicesUtils
from .utils import extract_size_name,add_commision,data_percentage_add
from django.conf import settings

from decimal import Decimal

GSUB_KEY =settings.GSUB_KEY
base_url ="https://gsubz.com/api"

headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GSUB_KEY}',  
        'Content-Type': 'application/x-www-form-urlencoded'
    }

returned_data= [
            {
                "displayName": "1GB - 7days",
                "value": "166",
                "price": 715,
                "service": "mtn_sme",
                "name": "MTN-SME-Data-",
                "qty": "1GB"
            },
 ]
            

def extract_data_qty(string):
    parts = string.split('-')
    if len(parts) > 1:
        return parts[0].strip()
    else:
        return None
def extract_data_qty(string):
     parts = string.split('-')
     if len(parts) > 1:
         return parts[0].strip()
     else:
         return None
# def normalise_data_cost(price):
#     origin_price = price /data_percentage_add
#     return price-round(origin_price,1)

def check_balance():
    payload={'api': GSUB_KEY}
    response = requests.post(f'{base_url}/balance/',headers = headers,data=payload, )
    result = response.json()
    # account,created = Account.objects.get_or_create(name ='PaysIt Balance')
    # account.data_balance= float(result['balance'])
    # account.save()


def affect_data_price(resulting_response,provider):
    all_plans = []
    # print(resulting_response)
    for plan_category in resulting_response:
        if plan_category and 'plans' in plan_category:
            for plan in plan_category['plans']:
                if 'price' in plan:
                    new_plan ={}
                    original_price = float(plan['price'])
                    #new_price = original_price * data_percentage_add
                    #new_price = round(new_price,1) 
                    #nomal_amount =math.ceil(new_price)
                    new_plan['price'] = add_commision(original_price)#nomal_amount
                    new_plan['provider_price'] = float(original_price)#nomal_amount
                    new_plan['provider']='GSUB'
                    new_plan['plan_id']=plan['value']
                    #new_plan['display_name']=plan['displayName']
                    new_plan['service_id'] =f"{plan['service']}"
                    new_plan['network']=provider.upper()
                    new_plan['name'] =f"{plan['service']}"
                    duration,_ =extract_size_name(plan['displayName'])
                    new_plan['duration']= duration
                    new_plan['qty']=extract_data_qty(plan['displayName'])    
                    all_plans.append(new_plan)
    return all_plans

async def fetch_data_plan_sync(session, service):
    async with session.get(f'{base_url}/plans/?service={service}', headers=headers) as response:
        try:
            res = await response.json()
            if res is not None:
                if res.get('plans'):
                    for plan in res['plans']:
                        plan['service'] = service
                    return res
            return None
        except Exception:
            return None

def fetch_data_plans(provider):
    providers ={
            "mtn":['mtncg', 'mtn_coupon', 'mtn_sme'],
            "airtel":["airtel_cg","airtel_sme"],
            "glo":['glo_data'],
            "etisalat": ["etisalat_data"]
    }
    service_list = providers[provider]
    async def main():
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_data_plan_sync(session, service) for service in service_list]
            responses = await asyncio.gather(*tasks)

            result = affect_data_price(responses,provider)
            return result
    return async_to_sync(main)()

def buy_data(data):
    
    payload={
    'serviceID': data['service_id'],
    'plan': data['plan_id'],
    'api': GSUB_KEY,
    'amount': round(float(data['price'])/float(1+(data_percentage_add/100)),1),
    'phone': data['phone_no'],
    'requestID':data['request_id']
    }
    # print(payload)
    
    try:
        response = requests.post(f'{base_url}/pay/',headers = headers,data=payload, )
        result = response.json()
        # print(result)
        status ="success"
        if result['code'] ==200 and result['status'] !="failed":
            status ="failed"
        elif result['status']=="failed":
            status = 'failed'
        else:
            status ="pending"
        return status

    except Exception as e:
        return "failed"

   

def buy_airtime(data):
    payload={'serviceID': data['service_id'],
    'api': GSUB_KEY,
    'amount': data['amount'],
    'phone': data['phone_no'],
    'requestID':data['request_id']}
    try: 
        response = requests.post(f'{base_url}/pay/',headers = headers,data=payload, files=[])
        result = response.json()
        status ="success"
        if result['code'] ==200 and result['status'] !="failed":
            status ="failed"
        elif result['status']=="failed":
            status = 'failed'
        else:
            status ="pending"
        return status
    except Exception as e:
        return False
  

def verify_transaction_status(request_id):
    payload={'requestID': request_id,
            'api': GSUB_KEY}
    # print(request_id)
    try:
        response = requests.post(f'{base_url}/verify/',headers = headers,data=payload, files=[])
        result = response.json()
        # print('inside gsub ', result)
        if result["code"]== "404":
            return False

        elif result["status"]== "success":
            return 'success'
            
        elif result["status"]== "pending":
            return 'pending'
        
        else:
            return 'failed'
        
        
    except Exception as e:
            # print(f"VTPass verification error: {e}")
            return "pending"
    