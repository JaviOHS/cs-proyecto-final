from django.urls import path
from app.security.views import auth, verify_2fa, manage_permissions
app_name = 'security'

urlpatterns = [
    path('signup/', auth.SignupView.as_view(), name='signup'),
    path('signin/', auth.SigninView.as_view(), name='signin'),
    path('signout/', auth.SignoutView.as_view(), name='signout'),
    path('verify-2fa/', verify_2fa.Verify2FAView.as_view(), name='verify_2fa'),
    path('verify-signup-2fa/', verify_2fa.VerifySignup2FAView.as_view(), name='verify_signup_2fa'),
    path('extend-session/', auth.ExtendSessionView.as_view(), name='extend_session'),
    path('manage/permissions/', manage_permissions.ManagePermissionsView.as_view(), name='manage_permissions'),
    path('user/update/<int:pk>/', manage_permissions.UserUpdateView.as_view(), name='user_update'),
    path('user/delete/<int:pk>/', manage_permissions.UserDeleteView.as_view(), name='user_delete'),
    path('group/create/', manage_permissions.GroupCreateView.as_view(), name='group_create'),
    path('group/update/<int:pk>/', manage_permissions.GroupUpdateView.as_view(), name='group_update'),
    path('group/delete/<int:pk>/', manage_permissions.GroupDeleteView.as_view(), name='group_delete'),
]
