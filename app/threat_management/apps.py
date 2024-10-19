from django.apps import AppConfig

class ThreatManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.threat_management'

    def ready(self):
        import app.threat_management.signals