from django.urls import path
from app.threat_management.views import detection

app_name = 'detection'

urlpatterns = [
    path('detection/', detection.DetectionListView.as_view(), name='detection_list'),
]
