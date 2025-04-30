from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
    

   path('create/',CreateVirtualCardView.as_view(),name='create_virtual_card'),
    path('update/cardholder/',UpdateCardholderView.as_view(),name='update_virtual_cardholder'),
    path('retrieve/cardholder/',CardHolderRetrieveView.as_view(),name='update_virtual_cardholder'),
     path('add/fund/',SwapFundToDollarCard.as_view(),name='add_card_fund'),
    # path('fund/payment/',PaymentWithStripeView.as_view(),name='fund_stripe_payment'),
    path('ephemeral/keys/',GenerateEphemeralKeys.as_view(),name='ephemeral_keys'),
    path('webhook/',virtualcard_webhook_view,name='stripe_webhook'),
    path('payment/webhook/',payment_webhook_view,name='stripe_payment_webhook'),
    path('authorization/webhook/',CardAuthorizationWebhook.as_view(),name='card_authorization_webhook'),

    
    
]
