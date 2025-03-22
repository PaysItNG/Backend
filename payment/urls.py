from django.urls import path
from .views import PaystackWebhook,BankList,BankTransfer,DedicatedAccountList,CreateDBAAPI

urlpatterns = [
    path("paystack-webhook/", PaystackWebhook.as_view(), name="paystackwh"),
    path('api/banks/', BankList.as_view(), name='bank-list'),#list of banks and their codes  
    path('bank/transfer/',BankTransfer.as_view(),name="bank-transfer"),#send money
    path('bank/accounts/',DedicatedAccountList.as_view(),name="bank-transfer"),#retrieve users DBA
    path('create/user/account/',CreateDBAAPI.as_view(), name ='create-dba'),
]
