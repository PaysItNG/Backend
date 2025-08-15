from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
  path('locations/',  AirportLocationSearchView.as_view(),name='airport_location'),
  # path('offers/',GetFlightOffersView.as_view(), name='flight_offers')
]
