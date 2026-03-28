from django.urls import path

from .views import (
    StudentVerificationApproveView,
    StudentVerificationStatusView,
    StudentVerificationSubmitView,
)


urlpatterns = [
    path('status/', StudentVerificationStatusView.as_view(), name='student_status'),
    path('submit/', StudentVerificationSubmitView.as_view(), name='student_submit'),
    path('approve/', StudentVerificationApproveView.as_view(), name='student_approve'),
]
