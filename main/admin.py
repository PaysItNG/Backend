from django.contrib import admin

# Register your models here.
from .models import *


admin.site.register(RoleInvite)

admin.site.register(User)
admin.site.register(UserProfile)
admin.site.register(Security)
admin.site.register(KYCVerification)
admin.site.register(Wallet)
admin.site.register(Transaction)
admin.site.register(BankDetails)
admin.site.register(Notification)