from django.urls import path
from app.monitoring.views import monitoring_session, real_time_monitoring, notifications

app_name = 'monitoring'

urlpatterns = [
    path('monitoring_session/', monitoring_session.MonitoringSessionView.as_view(), name='monitoring_session'),
    path('create_session/', monitoring_session.CreateMonitoringSessionView.as_view(), name='create_session'),
    path('real_time_view/<int:session_id>', real_time_monitoring.RealTimeMonitoringView.as_view(), name='real_time_view'),
    path('update_session/<int:pk>', monitoring_session.UpdateMonitoringSessionView.as_view(), name='update_session'),
    path('delete_session/<int:pk>', monitoring_session.DeleteMonitoringSessionView.as_view(), name='delete_session'),
    path('video_feed/<int:session_id>', real_time_monitoring.VideoStreamView.as_view(), name='video_feed'),
    path('get_notifications/<int:session_id>/', notifications.get_notifications, name='get_notifications'),
]
