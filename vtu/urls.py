from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
   path('validate/number/',ValidateNumberView.as_view(),name='validate_number'),
   path('service/variations/',GetServiceVariationsView.as_view(),name='service_variation'),
   path('pay/service/',PayVariationService.as_view(),name='service_variation'),
   path('webhook/',VtuWebhookView.as_view(),name='vtu_webhook')
]
