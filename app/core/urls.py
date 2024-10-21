from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app.core.views.home import HomeTemplateView
from app.core.views.profile_view import ProfileView, UserProfileUpdateView
from app.core.views.recuperation_email import PasswordResetView
from django.contrib.auth import views as auth_views
from .views.recuperation_email import CustomPasswordResetConfirmView
from app.core.views.scaner_face import FacialRecognitionView
from app.core.views.chatbot import ChatbotView
from app.core.views.graphs_view import StatisticalGraphsTemplate 
from app.core.views.statistics_format import Plantilla 
from django.utils.translation import gettext_lazy as _
from django.views.i18n import set_language
from app.core.views.error_page import ErrorPageTemplate
from app.core.views.open_api import OpenAIChatView
from app.core.views.user_settings import UserSettingsView
app_name = 'core'

urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('set_language/', set_language, name='set_language'),
    path('',HomeTemplateView.as_view(), name='home'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', UserProfileUpdateView.as_view(), name='profile_update'),
    path('password_reset/', PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('facial_recognition/', FacialRecognitionView.as_view(), name='facial_recognition'),
    path('api/chatbot/', ChatbotView.as_view(), name='chatbot_response'),
    path('statistics/', StatisticalGraphsTemplate.as_view(), name='statistics'),
    path('statistics_plantilla/', Plantilla.as_view(), name='statistics_plantilla'),
    path('error_page/', ErrorPageTemplate.as_view(), name='error_page'),
    path('api/chat/', OpenAIChatView.as_view(), name='openai_chat'),
    path('settings/', UserSettingsView.as_view(), name='user_settings'),
]
