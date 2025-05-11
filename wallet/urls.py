from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
    path('',UserWalletData.as_view(),name='user_wallet'),
    path('swap/currencies/',SwapCurrencyWalletFunds.as_view(),name='swap_wallet_currency'),
    path('paystack/webhook',PaystackWebhook,name='paystack_webhook'),
]
