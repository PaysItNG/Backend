from django.urls import path,re_path,include
from .views import *

urlpatterns=[
    path('role/invite',SendRoleInvite.as_view(),name='role_invite'),
    path('role/invite/accept',AcceptRoleInvite.as_view(),name='accept_invite'),
  
]