import amadeus.reference_data
import amadeus.reference_data.locations
from django.shortcuts import render
from amadeus import Client, ResponseError, Location
# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import (IsAuthenticated)
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from .utils import FlightUtils
from rest_framework import status

amadeus = Client(
    client_id=settings.AMADEUS_API_KEY,
    client_secret=settings.AMADEUS_SECRET
)

amadeus_utils=FlightUtils()


def get_city_airport_list(data):
    result = []
    for i, val in enumerate(data):
        result.append(data[i]['iataCode']+', '+data[i]['name'])
    result = list(dict.fromkeys(result))
    return result

class AirportLocationSearchView(APIView):
    permission_classes=[IsAuthenticated]
    authentication_classes=[JWTAuthentication]
    def post(self,request):
        location=str(request.data.get('location')).upper().strip()

        try:
            data = amadeus.reference_data.locations.get(keyword=location,
                                                         subType='AIRPORT,CITY').data
            return Response({
                'data':get_city_airport_list(data)
            })
        except ResponseError as error:
            return Response('') 
        



class GetFlightOffersView(APIView):
    def post(self,request):

        try:
            data=request.data
            response=amadeus_utils.search_offers(data=data)

            return Response({
                'data': response
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'message':f'an error occured at {e}'
            },status=status.HTTP_400_BAD_REQUEST)

