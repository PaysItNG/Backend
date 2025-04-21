import re
import requests
from django.conf import settings

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
    

    def GetServiceVariations(service_id):
        url=f'{base_url}service-variations?serviceID={service_id}'
        

        res=requests.get(url=url,headers=get_req_headers)

        # print(res.json())

        return res.json()