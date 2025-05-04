from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
    path('deposit',DepositFundsView.as_view(),name='deposit'),
    path('paystack/webhook',PaystackWebhook,name='paystack_webhook'),
]
