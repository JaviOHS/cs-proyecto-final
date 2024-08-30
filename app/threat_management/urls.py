from django.urls import path
from app.threat_management.views import detection

app_name = 'detection'

urlpatterns = [
    path('detection/', detection.DetectionListView.as_view(), name='detection_list'),
    path('detection/create/', detection.DetectionCreateView.as_view(), name='detection_create'),
    path('detection/update/<int:pk>/', detection.DetectionUpdateView.as_view(), name='detection_update'),
    path('detection/delete/<int:pk>/', detection.DetectionDeleteView.as_view(), name='detection_delete'),
]
