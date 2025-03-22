from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin,BaseUserManager
# Create your models here.
import uuid
import datetime
from django.utils import timezone

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password
import random
# from userauth.views import generateidentifier
import string
import json
# Create your models here.

def generateinviteID(length) ->str:
    val=''
    while len(val)<=length:
        val+=str(random.randint(0,9))
    
    return val

def generateWalletId(length)->str:
    char=string.ascii_lowercase+string.digits
    token="".join(random.choice(char) for _ in range(length))

    return token

def generateidentifier(length)->str:
    char=string.ascii_lowercase+string.digits
    token="".join(random.choice(char) for _ in range(length))

    return token



class UserManager(BaseUserManager):  # type: ignore

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin1')
        return self.create_user(email, password, **extra_fields)
    

class User(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES=(
        ('admin1','admin1'),
        ('admin','admin'),
        ('staff','staff'),
        ('merchant','merchant'),
        ('user','user')
    )
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50,null=True,blank=True)
    first_name = models.CharField(max_length=100,null=True,blank=True)
    last_name = models.CharField(max_length=100,null=True,blank=True)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    referral_id=models.CharField(max_length=100,null=True,blank=True)
    token=models.CharField(null=True,blank=True,max_length=1000)

    role=models.CharField(max_length=100,null=True,blank=True,choices=ROLE_CHOICES, default='user')
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    

class UserProfile(models.Model):
    Tiers=(
        ('tier1','tier1'),
        ('tier2','tier2'),
        ('tier3','tier3')
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    utility_bill=models.URLField(max_length=1000, blank=True, null=True)
    bvn=models.CharField(max_length=100, blank=True, null=True)
    tier=models.CharField(max_length=100,null=True,blank=True, choices=Tiers,default='tier1')
    referrals=models.ManyToManyField(User,related_name='referrals',blank=True)
    referee=models.ForeignKey(User,null=True,blank=True,on_delete=models.CASCADE,related_name='referee')
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.URLField( blank=True, null=True,max_length=5000)

    def __str__(self):
        return f"Profile of {self.user.email}"

    def save(self,*args,**kwargs):
        if self.bvn != None:
            self.tier='tier2'
        if  self.utility_bill != None :
            self.tier ='tier3'
        if self.utility_bill == None and self.bvn == None :
            self.tier='tier1'

        super().save(*args,**kwargs)


class KYCVerification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc')
    id_document =  models.URLField( blank=True, null=True,max_length=5000)
    selfie = models.URLField(max_length=5000, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,blank=True, null=True)
    submitted=models.BooleanField(default=False)
    submitted_at = models.DateTimeField(default='', blank=True,null=True)
    reviewed_at = models.DateTimeField(default='',blank=True,null=True)

    def __str__(self):
        return f"KYC Status for {self.user.email}: {self.status}"

    def save(self,*args,**kwargs):

        if self.status == 'verified' or 'rejected':
            self.reviewed_at=timezone.now()
        else:
            self.reviewed_at=None
        

        super().save(*args,**kwargs)




# User Activity Log Model
class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.timestamp}"


class Security(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE,null=True,blank=True)
    token=models.CharField(max_length=100,null=True,blank=True)
    locked = models.BooleanField(default=False)
    two_factor_auth_enabled = models.BooleanField(default=False)
    
    login_attempt_count = models.IntegerField(default=0)
    date_created=models.DateTimeField()
    
    class Meta:
        db_table = 'security'


    def save(self,*args,**kwargs):
       
        self.date_created=timezone.now()

        super().save(*args,**kwargs)




class RoleInvite(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    email=models.EmailField(max_length=100,null=True,blank=True)
    role=models.CharField(max_length=100,null=True,blank=True)
    identifier=models.CharField(max_length=100,null=True,blank=True)
    date_created=models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'{self.role} invite to {self.email}'


    def save(self,*args,**kwargs):
        token=generateinviteID(7)
        try:
            RoleInvite.objects.get(identifier=token)
        except ObjectDoesNotExist:
            
            self.identifier=f'py-{token}'

        user_emails=[user.email for user in list(User.objects.all())]

        if self.email in user_emails:
            self.user=User.objects.get(email=self.email)
        else:
            user=User.objects.create(
                email=self.email.strip(),
                username=self.email.strip(),
            )

            self.user=user
        super().save(*args,**kwargs)




class Wallet(models.Model):
    CURRENCY_CHOICES = [
    ('NGN', 'Nigerian Naira'),
    ('USD', 'US Dollar'),
    ('EUR', 'Euro'),]
    user=models.OneToOneField(User,on_delete=models.CASCADE,null=True,blank=True)
    wallet_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NGN')
    is_active=models.BooleanField(default=True)
    date_created=models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True)
    def __str__(self):
        return f'{self.user.email} Wallet'

    def save(self,*args,**kwargs):
        wallet_ids=list(x.wallet_id for x in Wallet.objects.all())
        if self.wallet_id == None:
            if self.wallet_id not in wallet_ids:
                self.wallet_id=f'@{generateWalletId(7)}'

    #     super().save(*args,**kwargs)
    # def save(self, *args, **kwargs):
    #     if not self.wallet_id:
    #         self.wallet_id = uuid.uuid4() 
        super().save(*args, **kwargs)




class Business(models.Model):
    owner=models.OneToOneField(User,null=True,blank=True,on_delete=models.CASCADE, related_name='business_owner')
    company_name=models.CharField(max_length=1000,null=True,blank=True)
    balance=models.FloatField(blank=True,null=True)
    staffs=models.ManyToManyField(User,related_name='company_staffs')
    date_created=models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'{self.company_name} owned by {self.owner.email}'



class BusinessTerminal(models.Model):
    user=models.OneToOneField(User,null=True,blank=True,on_delete=models.CASCADE)
    business=models.ForeignKey(Business,null=True,blank=True, on_delete=models.CASCADE)
   


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('deposit', 'deposit'),
        ('withdrawal', 'withdrawal'),
        ('transfer', 'transfer'),
        ('subscription', 'subscription')
    ]
    PAYMENT_TYPE=(
        ('debit','debit'),
        ('credit','credit'),
    )
    STATUS_CHOICES = [
        ('pending', 'pending'),
        ('completed', 'completed'),
   
        ('processing', 'processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    to_from =models.CharField(max_length=15,null=True,blank=True)
    sender_name =models.CharField(max_length=25, null=True,blank=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE, )
    paystack_data=models.JSONField(max_length=50000,null=True,blank=True)
    paystack_ref=models.CharField(max_length=100,null=True,blank=True)
    description = models.TextField(default="")
    reference_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} {self.user.email} ({self.status})"
    
    def save(self,*args,**kwargs):
        ref_id=generateidentifier(10)

        debit_transaction_types=['withdrawal','transfer','subscription']
        if self.paystack_data!= None:
            self.paystack_ref=json.loads(self.paystack_data)['data']['reference']
        if self.transaction_type not in debit_transaction_types:
            self.payment_type='credit'
        else:
            self.payment_type='debit'

            
        if self.reference_id == None:
            try:
                Transaction.objects.get(reference_id=ref_id)

            except ObjectDoesNotExist:
                self.reference_id=ref_id

        super().save(*args,**kwargs)

class BankDetails(models.Model):
    user=models.ForeignKey(User,null=True,blank=True,on_delete=models.CASCADE)
    account_holder_name=models.CharField(
        max_length=200,null=True,blank=True
    )
    account_number=models.CharField(max_length=200,null=True,blank=True)
    bank_name=models.CharField(max_length=200,null=True,blank=True)
    routing_number=models.CharField(max_length=200,null=True,blank=True)
    card_number=models.CharField(max_length=200,null=True,blank=True)
    is_primary=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True,)
    updated_at=models.DateTimeField(auto_now=True,)


    def __str__(self):
        return f'{self.user.email} bank details'

class Notification(models.Model):
    user=models.ForeignKey(User,null=True,blank=True,on_delete=models.CASCADE)
    message=models.CharField(max_length=1000,null=True,blank=True)
    is_read=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.user.email}'





class Card(models.Model):
    user=models.ForeignKey(User,null=True,blank=True,on_delete=models.CASCADE)
    card_holder_ref_id=models.CharField(max_length=1000,null=True,blank=True)
    card_ref_id=models.CharField(max_length=1000,null=True,blank=True)
    card_number=models.CharField(max_length=200,null=True,blank=True)
    card_holder_name=models.CharField(max_length=200,null=True,blank=True)
    expiry_date=models.DateField(null=True,blank=True)
    cvv=models.CharField(max_length=10,null=True,blank=True)
    card_type=models.CharField(max_length=100,null=True,blank=True)
    card_brand=models.CharField(max_length=100,null=True,blank=True)
    last_four=models.CharField(max_length=100,null=True,blank=True)
    
    status=models.CharField(max_length=100,null=True,blank=True)
    issued=models.BooleanField(default=False)
    is_primary=models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

