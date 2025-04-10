from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import *

@receiver(post_save,sender=Transaction)
def TransactionNotification(sender,instance,created,**kwargs):
    
    if instance.status == 'completed' or instance.status == 'failed':
        message=f'{instance.amount} {instance.transaction_type}-{str(instance.status).upper()}'
        Notification.objects.create(
            user=instance.user,
            message=message,
        ) 