from rest_framework import serializers

from rest_framework_simplejwt.tokens import RefreshToken
from main.models import *

def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model=User
        fields = ['email', 'password','role','id','first_name','is_active','last_name','is_staff','is_superuser','profile']
        extra_kwargs = {'password': {'write_only': True},'is_staff': {'read_only': True},
                        'is_active': {'read_only': True},'is_superuser': {'read_only': True},
                        'role':{'read_only':True},'profile':{'read_only':True}
                        }
        
    def create(self, validated_data):
       

        user = User.objects.create(email=str(validated_data['email']).lower(),
        username=str(validated_data['email']).lower(),
        # first_name=str(validated_data['first_name']).lower(),last_name=str(validated_data['last_name']).lower()
        )
        user.set_password(validated_data['password'])
        user.save()

        # user_profile=UserProfile.objects.create(user=user)
        # kyc=KYCVerification.objects.create(user=user)

        token=get_tokens_for_user(user)
        # print(token)
        return user
    
    




class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserProfile
        fields="__all__"





class KYCVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model=KYCVerification
        fields="__all__"
        extra_kwargs={'user':{'read_only':True},
                      'status':{'read_only':True},
                      'submitted_at':{'read_only':True},
                      'reviewed_at':{'read_only':True}}






class UserActivityLogSerializer(serializers.ModelSerializer):
    class Meta:
        model=UserActivityLog
        fields="__all__"



class SecuritySerializer(serializers.ModelSerializer):
    class Meta:
        model=Security
        fields="__all__"

class RoleInviteSerializer(serializers.ModelSerializer):
    class Meta:
        model=RoleInvite
        fields="__all__"



class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model=Wallet
        fields="__all__"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Transaction
        fields="__all__"




class Cardserializer(serializers.ModelSerializer):
    class Meta:
        model=Card
        fields="__all__"