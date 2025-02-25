from rest_framework import serializers
from .models import *

class RoleInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model=RoleInvite
        fields="__all__"