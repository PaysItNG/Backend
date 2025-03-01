from django.db import models
from django.contrib.auth.models import AbstractBaseUser,PermissionsMixin,BaseUserManager
# Create your models here.
import uuid
import datetime
from django.utils import timezone

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.hashers import make_password

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
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    role=models.CharField(max_length=100,null=True,blank=True,choices=ROLE_CHOICES, default='user')
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email
    

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_picture = models.URLField( blank=True, null=True,max_length=5000)

    def __str__(self):
        return f"Profile of {self.user.email}"


class KYCVerification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='kyc')
    id_document =  models.URLField( blank=True, null=True,max_length=5000)
    selfie = models.URLField(max_length=5000, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES,)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"KYC Status for {self.user.email}: {self.status}"



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
