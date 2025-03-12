from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class PaystackCustomer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="paystack_account")
    customer_id = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Paystack Customer ID
    recipient_code = models.CharField(max_length=50, unique=True, null=True, blank=True)  # Paystack Recipient Code
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.customer_id or 'No Paystack ID'}"


class DedicatedAccount(models.Model):
    paystack_account = models.ForeignKey(PaystackCustomer, on_delete=models.CASCADE, related_name="dedicated_accounts")
    bank_name = models.CharField(max_length=100)
    account_number = models.CharField(max_length=15, unique=True)
    account_name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.bank_name} -| {self.account_number}"


class PaystackRecipient(models.Model):
    #user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="paystack_recipients")
    recipient_code = models.CharField(max_length=50, unique=True)
    bank_name = models.CharField(max_length=100)
    bank_code = models.CharField(max_length=10)
    account_number = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.bank_name} ({self.account_number})"