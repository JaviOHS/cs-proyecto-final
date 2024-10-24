from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import pygame
from app.alarm.utils import validate_sound_file
from app.threat_management.models import Detection
import requests
import io

pygame.init()

def play_audio_from_s3(url):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        audio_data = io.BytesIO(response.content)
        try:
            pygame.mixer.music.load(audio_data)
            pygame.mixer.music.play()
        except Exception as e:
            print(f"Error al reproducir con pygame: {e}\nIntentando reproducir con pydub...")

    except requests.RequestException as e:
        print(f"Error al obtener el archivo de audio: {e}")
    except Exception as e:
        print(f"Error inesperado: {e}")

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

    class Meta:
        unique_together = ('user', 'detection')
        verbose_name = "Alarma"
        verbose_name_plural = "Alarmas"
        
    def clean(self):
        if self.sound_file:
            validate_sound_file(self.sound_file)

    def save(self, *args, **kwargs):
        if self.pk:
            old_alarm = Alarm.objects.get(pk=self.pk)
            if old_alarm.sound_file and old_alarm.sound_file != self.sound_file:
                if Alarm.alarm_sound_playing:
                    self.stop_alarm()
                if old_alarm.sound_file.name != 'alarms/alarma_defecto.mp3':
                    old_alarm.sound_file.delete(save=False)

        if not self.notification_message:
            self.notification_message = f"Se ha detectado una amenaza de {self.detection.name}."

        if not self.sound_file:
            self.sound_file = 'alarms/alarma_defecto.mp3'

        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Alarma para {self.detection.name}"

    def get_sound_file(self):
        if self.sound_file:
            return self.sound_file.url
        return 'alarms/alarma_defecto.mp3'

    def activate(self):
        self.last_activated = timezone.now()
        self.save()
        if not Alarm.alarm_sound_playing:
            sound_file_url = self.get_sound_file()
            play_audio_from_s3(sound_file_url)
            Alarm.alarm_sound_playing = True

    @staticmethod
    def stop_alarm():
        Alarm.alarm_sound_playing = False
        pygame.mixer.music.stop()

    def create_alarm(self, detection, user):
        try:
            print(f"Creando alarma para la detección '{detection.name}' y el usuario '{user.username}'...")
            new_alarm = Alarm(
                detection=detection,
                user=user,
                is_active=True,
                notification_message=f"Se ha detectado una amenaza de {detection.name}."
            )
            new_alarm.save()
            print(f"Alarma creada exitosamente para la detección '{detection.name}' y el usuario '{user.username}'.")
            return new_alarm
        except ValidationError as e:
            print(f"Error al crear la alarma: {e}")
            return None
