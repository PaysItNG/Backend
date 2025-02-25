from django.urls import path
from .views import *
from django.conf.urls.static import static
from django.conf import settings



urlpatterns = [
    path('register',SignupView.as_view(),name='register'),
    path('login',LoginView.as_view(),name='login')
]
