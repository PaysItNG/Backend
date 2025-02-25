from django.db import models
from userauth.models import *
import random
from django.core.exceptions import ObjectDoesNotExist
# Create your models here.

def generateinviteID(length):
    val=''
    while len(val)<=length:
        val+=str(random.randint(0,9))
    
    return val



class RoleInvite(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    email=models.EmailField(max_length=100,null=True,blank=True)
    role=models.CharField(max_length=100,null=True,blank=True)
    identifier=models.CharField(max_length=100,null=True,blank=True)
    date_created=models.DateTimeField(auto_now=True)


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