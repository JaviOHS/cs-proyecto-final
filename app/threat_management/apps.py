from django.apps import AppConfig
from django.db.models.signals import post_migrate

class ThreatManagementConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app.threat_management'

    def ready(self):
        post_migrate.connect(create_default_detection_models, sender=self)

def create_default_detection_models(sender, **kwargs):
    from .models import Detection
    
    default_models = [
        {"name": "Robos Inesperados", "icon": "fa-solid fa-user-ninja","description": "Detecta cuando un individuo guarda pertenencias ajenas en bolsos, bolsillos o en su cuerpo."},
        {"name": "Pérdidas Inesperadas", "icon": "fa-solid fa-box", "description": "Detecta cuando un individuo pierde objetos de manera inesperada, como caídas de pertenencias."}
    ]
    
    for model_data in default_models:
        Detection.objects.get_or_create(name=model_data['name'], defaults=model_data)