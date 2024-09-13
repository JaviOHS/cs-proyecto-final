import os
from django.conf import settings
import pygame
from django.db import models
from django.utils import timezone
from app.alarm.utils import validate_sound_file
from app.threat_management.models import Detection

class Alarm(models.Model):
    detection = models.OneToOneField(Detection, on_delete=models.CASCADE, verbose_name='Amenaza a Detectar')
    sound_file = models.FileField(upload_to='alarms/', verbose_name='Archivo de Alarma', blank=True, null=True)
    notification_message = models.TextField(max_length=200, verbose_name='Mensaje de Notificación', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuario')
    last_activated = models.DateTimeField(null=True, blank=True, verbose_name='Última activación')

    # Variable estática para indicar si la alarma está sonando
    alarm_sound_playing = False

    def clean(self):
        if self.sound_file:
            validate_sound_file(self.sound_file)

    def save(self, *args, **kwargs):
        if not self.sound_file:
            self.sound_file = 'alarms/default_alarm.mp3'
        if not self.notification_message:
            self.notification_message = f"Se ha detectado una amenaza de tipo {self.detection.name}."
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Alarma para {self.detection.name}"

    def activate(self):
        self.last_activated = timezone.now()
        self.save()
        # Iniciar pygame mixer solo si el sonido no está ya en reproducción
        if not Alarm.alarm_sound_playing:
            if self.sound_file:
                sound_file_path = os.path.join(settings.MEDIA_ROOT, self.sound_file.name)
                pygame.mixer.init()
                pygame.mixer.music.load(sound_file_path)
                pygame.mixer.music.play(loops=-1)  # Reproducir en bucle
                Alarm.alarm_sound_playing = True

    @staticmethod
    def stop_alarm():
        # Detener la alarma si está en reproducción
        if Alarm.alarm_sound_playing:
            pygame.mixer.music.stop()
            Alarm.alarm_sound_playing = False

    class Meta:
        verbose_name = "Alarma"
        verbose_name_plural = "Alarmas"