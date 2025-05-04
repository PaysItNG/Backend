from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
   path('validate/phone-number/',ValidateNumberView.as_view(),name='validate_number'),
   path('vtu/services/',AirtimeDataVariationService.as_view(),name='service_variation'),
   path('verify/meter/',VerifyMeterNumberView.as_view(),name='verify_meter_no'),
   path('pay/utility/',PayUtilityVariationService.as_view(),name='pay_utility'),
   path('webhook/',VtuWebhookView.as_view(),name='vtu_webhook')
]
