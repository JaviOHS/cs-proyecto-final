from django.urls import path
from app.security.views import auth

app_name = "security"
urlpatterns = [
    path('auth/login/',auth.signin,name="auth_login"),
    path('auth/signup/',auth.signup,name='auth_signup'),
    path('auth/logout/',auth.signout,name='auth_logout'),
]