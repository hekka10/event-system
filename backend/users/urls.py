from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    CustomTokenObtainPairView,
    GoogleOAuthLoginView,
    RegisterView,
    StudentVerificationAdminListView,
    StudentVerificationReviewView,
    StudentVerificationSubmissionView,
    UserProfileView,
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('google/', GoogleOAuthLoginView.as_view(), name='google_login'),
    path('me/', UserProfileView.as_view(), name='me'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path(
        'student-verifications/',
        StudentVerificationSubmissionView.as_view(),
        name='student_verification_submission',
    ),
    path(
        'student-verifications/admin/',
        StudentVerificationAdminListView.as_view(),
        name='student_verification_admin_list',
    ),
    path(
        'student-verifications/<uuid:pk>/review/',
        StudentVerificationReviewView.as_view(),
        name='student_verification_review',
    ),
]
