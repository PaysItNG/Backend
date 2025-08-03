
from django.contrib.auth.backends import ModelBackend

from django.contrib.auth import get_user_model
User = get_user_model()#get the user model used for the entire project


'''
This class is responsible for user login
permiting them to user username,email and phone number to login
'''
class EmailUsernameAuthBackend(ModelBackend):
    def authenticate(self,request,username =None, password = None):
        try:
            user = User.objects.get(email=username)
            success = user.check_password(password)
            if success:
                return user
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username)
                success = user.check_password(password)
                if success:
                    return user
            except User.DoesNotExist:
                    return None

#user use phone number to login
class EmailUsernamePhoneAuthBackend(ModelBackend):
    def authenticate(username =None, password = None):
        try:
            user = User.objects.get(email=username)
            success = user.check_password(password)
            if success:
                return user
        except User.DoesNotExist:
            try:
                user = User.objects.get(username=username)
                success = user.check_password(password)
                if success:
                    return user
            except User.DoesNotExist:
                try:
                    user = User.objects.get(phone_number=username)
                    success = user.check_password(password)
                    if success:
                        return user
                except User.DoesNotExist:
                    return None

    def get_user(self, user_id):
        """ Get a User object from the user_id. """
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None