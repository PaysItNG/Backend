from django.urls import path,re_path,include
from .views import *

urlpatterns=[
    path('role/invite',SendRoleInvite.as_view(),name='role_invite'),
    path('role/invite/accept',AcceptRoleInvite.as_view(),name='accept_invite'),
    path('kyc/status',KycStatusView.as_view(),name='kyc_status'),
    path('kyc/approve/<str:id>',ApproveKycView.as_view(),name='kyc_approve'),
  
]