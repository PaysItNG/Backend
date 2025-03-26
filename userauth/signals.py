from django.contrib.auth import get_user_model
from django.dispatch import receiver
from django.db.models.signals import post_save
from main.models import *
from django.contrib.auth.hashers import make_password
from django.core.mail import send_mail
from main.models import UserProfile
from django.template.loader import render_to_string
from django.conf import settings

host_user = settings.EMAIL_HOST_USER

User=get_user_model()
token=generateinviteID(5)

def send_user_message(subject, message, user):
        mail_subject = subject
        message = render_to_string( "message.html", {
            'subject':subject,
            'user': user,
            'message': message,
                  })
        from_email = f'{subject} <{host_user}>'
        to_email = user.email
        send_mail(mail_subject, message, from_email, [to_email], html_message=message)
        

@receiver(post_save,sender=User)
def CreateUserProfile(sender, instance, created, **kwargs):
    if created:
        
        UserProfile.objects.create(user=instance)
        Wallet.objects.create(user=instance)
