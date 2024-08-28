from django.urls import path
from app.security.views import auth
app_name = 'security'

urlpatterns = [
    path('signup/', auth.SignupView.as_view(), name='signup'),
    path('signin/', auth.SigninView.as_view(), name='signin'),
    path('signout/', auth.SignoutView.as_view(), name='signout'),
]
