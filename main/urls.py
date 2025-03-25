from django.urls import path
from .views import APIendpoints
urlpatterns = [
    path("",APIendpoints)
]