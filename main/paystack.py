import requests
from django.conf import settings

def PaystackVerify(data,profile=None):
    url=f'https://api.paystack.co/transaction/verify/{data['reference']}'
    headers={
        "Authorization":f"Bearer {settings.PSTACK_SECRET_KEY}"
    }
    res=requests.get(url=url,headers=headers)
    print(res.json())

    return res.json()