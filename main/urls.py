from django.urls import path
from .views import *
urlpatterns = [
    path("",APIendpoints),
    path('profile/',UserProfileDataView.as_view(),name='profile')
]