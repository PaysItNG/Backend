from django.urls import path
from .views import PaystackWebhook

urlpatterns = [
    path("paystack-webhook/", PaystackWebhook.as_view(), name="paystackwh"),
]
