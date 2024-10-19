from django.db.models.signals import post_migrate
from django.dispatch import receiver
from app.threat_management.models import Detection

@receiver(post_migrate)
def create_default_detection_models(sender, **kwargs):
    default_models = [
        {"name": "Robos Inesperados", "icon": "fa-solid fa-user-ninja", "description": "Detecta cuando un individuo guarda pertenencias ajenas en bolsos, bolsillos o en su cuerpo."},
        {"name": "Objetos Caidos", "icon": "fa-solid fa-box", "description": "Detecta apariciones de objetos, como caídas de pertenencias."},
        {"name": "Aglomeraciones", "icon": "fa-solid fa-users", "description": "Detecta cuando existen aglomeraciones de personas en un espacio."},
        {"name": "Detectar Movimiento", "icon": "fa-solid fa-running", "description": "Detecta movimiento en un espacio."},
        {"name": "Detectar Agresiones", "icon": "fa-solid fa-fist-raised", "description": "Detecta agresiones físicas entre personas."},
        {"name": "Detectar Armas", "icon": "fa-solid fa-shield-alt", "description": "Detecta la presencia de armas en un espacio."},
    ]
    
    for model_data in default_models:
        Detection.objects.get_or_create(name=model_data['name'], defaults=model_data)
