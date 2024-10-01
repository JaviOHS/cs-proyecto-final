import os
from django.conf import settings
import pygame
from django.db import models
from django.utils import timezone
from app.alarm.utils import validate_sound_file
from app.threat_management.models import Detection

class Alarm(models.Model):
    detection = models.ForeignKey(Detection, on_delete=models.CASCADE, verbose_name='Amenaza a Detectar')
    sound_file = models.FileField(upload_to='alarms/', verbose_name='Archivo de Alarma', blank=True, null=True)
    notification_message = models.TextField(max_length=200, verbose_name='Mensaje de Notificación', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Creación')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Fecha de Actualización')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name='Usuario')
    last_activated = models.DateTimeField(null=True, blank=True, verbose_name='Última activación')
    alarm_sound_playing = False

    def clean(self):
        if self.sound_file:
            validate_sound_file(self.sound_file)

    def save(self, *args, **kwargs):
        if self.pk:
            old_alarm = Alarm.objects.get(pk=self.pk)
            if old_alarm.sound_file and old_alarm.sound_file != self.sound_file:
                if Alarm.alarm_sound_playing:
                    self.stop_alarm()
                if old_alarm.sound_file != 'alarms/default_alarm.mp3':
                    old_sound_file_path = os.path.join(settings.MEDIA_ROOT, old_alarm.sound_file.name)
                    if os.path.exists(old_sound_file_path):
                        try:
                            os.remove(old_sound_file_path)
                        except PermissionError as e:
                            raise
                        
        if not self.notification_message:
            self.notification_message = f"Se ha detectado una amenaza de {self.detection.name}."
            
        if not self.sound_file:
            self.sound_file = 'alarms/default_alarm.mp3'

        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Alarma para {self.detection.name}"

    def activate(self):
        self.last_activated = timezone.now()
        self.save()

        if not Alarm.alarm_sound_playing:
            if self.sound_file:
                sound_file_path = os.path.join(settings.MEDIA_ROOT, self.sound_file.name)
                pygame.mixer.init()
                pygame.mixer.music.load(sound_file_path)
                pygame.mixer.music.play(-1)
                Alarm.alarm_sound_playing = True
                pygame.mixer.music.set_endevent(pygame.USEREVENT)

    @staticmethod
    def stop_alarm():
        if Alarm.alarm_sound_playing:
            pygame.mixer.music.stop()
            Alarm.alarm_sound_playing = False
            
    def play_default_alarm(self):
        default_sound_file_path = os.path.join(settings.MEDIA_ROOT, 'alarms/default_alarm.mp3')

        if not os.path.exists(default_sound_file_path):
            raise FileNotFoundError("El archivo de sonido de alarma por defecto no se encuentra.")

        if not Alarm.alarm_sound_playing:
            pygame.mixer.init()
            pygame.mixer.music.load(default_sound_file_path)
            pygame.mixer.music.play(-1)
            Alarm.alarm_sound_playing = True
            pygame.mixer.music.set_endevent(pygame.USEREVENT)
            
    class Meta:
        verbose_name = "Alarma"
        verbose_name_plural = "Alarmas"