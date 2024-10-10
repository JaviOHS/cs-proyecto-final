from django.db import models
from django.conf import settings

class Detection(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nombre de Amenaza', unique=True)
    description = models.TextField(max_length=500, verbose_name='Descripción', blank=True, null=True)
    icon = models.CharField(max_length=100, verbose_name='Ícono', blank=True, null=True, default='fa-solid fa-exclamation-triangle')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Modelo de Detección de Amenaza"
        verbose_name_plural = "Modelos de Detección de Amenazas"
    
    def save(self, *args, **kwargs):
        if not self.icon:
            self.icon = 'fa-solid fa-exclamation-triangle'
        if not self.description:
            self.description = 'No se ha proporcionado una descripción.'
        super().save(*args, **kwargs)
        
class DetectionCounter(models.Model):
    detection = models.ForeignKey('Detection', on_delete=models.CASCADE, verbose_name='Amenaza Detectada')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuario')
    count = models.PositiveIntegerField(default=0, verbose_name='Cantidad de Detecciones')

    class Meta:
        unique_together = ('detection', 'user')
        verbose_name = 'Contador de Detecciones'
        verbose_name_plural = 'Contadores de Detecciones'

    def increment(self):
        self.count += 1
        self.save()

    def __str__(self):
        return f"{self.detection.name} - {self.user.username} - {self.count} detecciones"