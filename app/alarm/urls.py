from django.urls import path
from app.alarm.views import alarm

app_name = 'alarm'

urlpatterns = [
    path('alarm/', alarm.AlarmListView.as_view(), name='alarm_list'),
    path('alarm/create/', alarm.AlarmCreateView.as_view(), name='alarm_create'),
    path('alarm/update/<int:pk>/', alarm.AlarmUpdateView.as_view(), name='alarm_update'),
    path('alarm/delete/<int:pk>/', alarm.AlarmDeleteView.as_view(), name='alarm_delete'),
]
