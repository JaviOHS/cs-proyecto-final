from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app.core.views.home import HomeTemplateView
from app.core.views.error_page import custom_404_view, custom_500_view

urlpatterns = [
    path('', HomeTemplateView.as_view(), name='home'),
    path('core/', include('app.core.urls')),
    path('admin/', admin.site.urls),
    path('security/', include('app.security.urls', namespace='security')),
    path('monitoring/', include('app.monitoring.urls', namespace='monitoring')),
    path('detection/', include('app.threat_management.urls', namespace='detection')),
    path('alarm/', include('app.alarm.urls', namespace='alarm')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = custom_404_view
handler500 = custom_500_view