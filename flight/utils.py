from django.conf import settings
import requests


base_url='https://test.api.amadeus.com/v2'


class FlightUtils():
    def __init__(self):
        self.access_token = self.get_access_token()
        self.headers={'Authorization':f'Bearer {self.access_token}'}

    def get_access_token(self):
        url = f"https://test.api.amadeus.com/v1/security/oauth2/token"
        data = {
            'grant_type': 'client_credentials',
            'client_id': settings.AMADEUS_API_KEY,
            'client_secret': settings.AMADEUS_SECRET
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        return response.json().get('access_token')



    def search_offers(self,data):
       
        params={
            'originLocationCode':data['origin'],
            'destinationLocationCode':data['destination'],
            'departureDate':data['departure'],
            'returnDate':data['arrival'],
            'adults':data.get('adults',1),
            'infants':data.get('infants',0),
            'travelClass':str(data.get('class')).upper(),
            'currencyCode':str(data.get('currency')).upper()

        }
        url=f'{base_url}/shopping/flight-offers'
        res=requests.get(url=url,params=params, headers=self.headers)
        return res.json()

