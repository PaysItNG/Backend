from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
    path('register',SignupView.as_view(),name='register'),
    path('activate/account',VerifyActiveStatusView.as_view(),name='activate_account'),
    path('login',LoginView.as_view(),name='login'),
    path('verify/social',VerifySocialLogin,name='verify_social'),
    path('password/change',RequestPasswordChangeView.as_view(),name='password_change'),
     path('password/verify',VerifyPasswordRequestChangeView.as_view(),name='password_verify'),
     path('kyc/apply',KycVerificationView.as_view(),name='kyc_apply'),
]
