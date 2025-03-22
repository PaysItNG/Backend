from django.contrib import admin
from .models import PaystackCustomer,PaystackRecipient,DedicatedAccount
# Register your models here.
admin.site.register(PaystackCustomer)
admin.site.register(DedicatedAccount)
admin.site.register(PaystackRecipient)