from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save
from main.models import *

# User=get_user_model()

@receiver(post_save,sender=User)
def CreateUserProfile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
        Wallet.objects.create(user=instance)
