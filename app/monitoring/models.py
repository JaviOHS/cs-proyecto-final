import os
from django.conf import settings
from django.db import models
from app.threat_management.models import Detection

class MonitoringSession(models.Model):
    name = models.CharField(max_length=100, null=True, verbose_name='Nombre', unique=True)
    description = models.TextField(null=True, blank=True, verbose_name='Descripción')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    detection_models = models.ManyToManyField(Detection, verbose_name='Modelos de Detección')
    crowding_threshold = models.IntegerField(
        default=10,
        verbose_name='Umbral de Aglomeración',
        help_text='Número de personas a partir del cual se considera aglomeración'
    )

    def save(self, *args, **kwargs):
        if not self.description:
            self.description = 'No se ha proporcionado una descripción.'
        super().save(*args, **kwargs)
        
    class Meta:
        verbose_name = "Sesión de Monitoreo"
        verbose_name_plural = "Sesiones de Monitoreo"
            
    def __str__(self):
        return f"Session {self.id} - {self.user.username}"

def get_upload_path(instance, filename):
    return os.path.join('theft_evidence', f'session_{instance.session.id}', filename)

class VideoEvidence(models.Model):
    session = models.ForeignKey(MonitoringSession, on_delete=models.CASCADE, related_name='video_evidences')
    video_file = models.FileField(upload_to=get_upload_path, null=True, blank=True, verbose_name='Evidencia de Video')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Evidencia de Video"
        verbose_name_plural = "Evidencias de Video"

    def __str__(self):
        return f"Video {self.id} - Session {self.session.id}"

