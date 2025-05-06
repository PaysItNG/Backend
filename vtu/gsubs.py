import requests
import asyncio
import aiohttp
from asgiref.sync import async_to_sync
import asyncio
import math

from django.conf import settings

GSUB_KEY =settings.GSUB_KEY
data_percentage_add = 10 # add 10%
base_url ="https://gsubz.com/api"

headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GSUB_KEY}',  
        'Content-Type': 'application/x-www-form-urlencoded'
    }

def extract_data_qty(string):
    parts = string.split('-')
    if len(parts) > 1:
        return parts[0].strip()
    else:
        return None

# def nomalise_data_cost(price):
#     origin_price = price /data_percentage_add
#     return price-round(origin_price,1)

def top_percentage(original_price,topup_pecentage):
    toped_ammount = original_price * topup_pecentage/100
    return original_price+toped_ammount

def check_balance():
    payload={'api': GSUB_KEY}
    response = requests.post(f'{base_url}/balance/',headers = headers,data=payload, )
    result = response.json()
    # account,created = Account.objects.get_or_create(name ='PaysIt Balance')
    # account.data_balance= float(result['balance'])
    # account.save()


def affect_data_price(resulting_response):
    all_plans = []
    for plan_category in resulting_response:
        if plan_category and 'plans' in plan_category:
            for plan in plan_category['plans']:
                if 'price' in plan:
                    original_price = float(plan['price'])
                    new_price = top_percentage(original_price,data_percentage_add)#original_price * data_percentage_add
                    new_price = round(new_price,1) 
                    nomal_amount =math.ceil(new_price)
                    plan['price'] = nomal_amount
                    plan['name'] =f"{plan_category['service'][:13]}"
                    plan['qty'] =extract_data_qty(plan['displayName'])
                    all_plans.append(plan)

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
    async def main():
        if provider in providers.keys():

            service_list = providers[provider]

            async with aiohttp.ClientSession() as session:
                tasks = [fetch_data_plan_sync(session, service) for service in service_list]
                responses = await asyncio.gather(*tasks)
                result = affect_data_price(responses)
                return result
        return "invalid provider or service_id"
        
    return async_to_sync(main)()

def buy_data(data,txn):
   
    payload={
    'serviceID': data['choice']['service'],
    'plan': data['plan'],
    'api': GSUB_KEY,
    'amount': '',
    'phone': data['phone'],
    'requestID':txn['txn_id']}
    try:
        response = requests.post(f'{base_url}/pay/',headers = headers,data=payload, )
        result = response.json()
        if result['code'] ==200:
            return True
        else:
            return False
    except Exception as e:
        return False

   

def buy_airtime(data,txn):
    payload={'serviceID': data['network'].lower(),
    'api': GSUB_KEY,
    'amount': data['amount'],
    'phone': data['phone'],
    'requestID': txn['txn_id']}   
    try: 
        response = requests.post(f'{base_url}/pay/',headers = headers,data=payload, files=[])
        result = response.json()
        if result['code'] ==200:
            return True
        else:
            return False
    except Exception as e:
        return False
  

async def verify_transaction(txn):
    payload={'requestID': txn.txn_id,
            'api': GSUB_KEY}
    try:
        response = requests.post(f'{base_url}/verify/',headers = headers,data=payload, files=[])
        result = response.json()
        if result["status"]== "success":
            return True
        else:
            return False
    except Exception:
        pass#return Falseimport requests
    
    