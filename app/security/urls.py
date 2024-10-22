from django.urls import path
from app.security.views import auth, verify_2fa
app_name = 'security'

urlpatterns = [
    path('signup/', auth.SignupView.as_view(), name='signup'),
    path('signin/', auth.SigninView.as_view(), name='signin'),
    path('signout/', auth.SignoutView.as_view(), name='signout'),
    path('verify-2fa/', verify_2fa.Verify2FAView.as_view(), name='verify_2fa'),
    path('verify-signup-2fa/', verify_2fa.VerifySignup2FAView.as_view(), name='verify_signup_2fa'),
]
