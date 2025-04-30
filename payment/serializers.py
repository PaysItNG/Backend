from rest_framework import serializers  
from .models import DedicatedAccount  

class DedicatedAccountSerializer(serializers.ModelSerializer):  
    class Meta:  
        model = DedicatedAccount  
        fields = ['id', 'bank_name', 'account_number', 'account_name', 'is_active', 'created_at', 'updated_at']  