from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from app.core.views.home import HomeTemplateView

urlpatterns = [
    path('',HomeTemplateView.as_view(), name='home'),
    path('admin/', admin.site.urls),
    path('security/', include('app.security.urls', namespace='security')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
