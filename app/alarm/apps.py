from django.apps import AppConfig
from django.db.models.signals import post_migrate

class AlarmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.alarm'
    