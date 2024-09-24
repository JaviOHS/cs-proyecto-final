import os
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from threading import Timer
from .models import MonitoringSession, VideoEvidence
from config.utils import RED_COLOR, GREEN_COLOR, YELLOW_COLOR, RESET_COLOR, BLUE_COLOR, GREY_COLOR
import shutil

DELETE_DELAY = 15 * 60

def delete_files_and_directory(session):
    session_directory = os.path.join('theft_evidence', f'session_{session.id}')
    for video_evidence in session.video_evidences.all():
        if video_evidence.video_file and os.path.exists(video_evidence.video_file.path):
            os.remove(video_evidence.video_file.path)
        video_evidence.delete()
    full_path = os.path.join(settings.MEDIA_ROOT, session_directory)
    if os.path.exists(full_path):
        try:
            shutil.rmtree(full_path)
            print(YELLOW_COLOR + f"Directorio {full_path} eliminado correctamente." + RESET_COLOR)
        except OSError as e:
            print(RED_COLOR + f"Error al eliminar el directorio {full_path}: {e}" + RESET_COLOR)

@receiver(pre_delete, sender=MonitoringSession)
def delete_session_files_and_directory(sender, instance, **kwargs):
    delete_files_and_directory(instance)
    print(BLUE_COLOR + f"Todos los archivos y el directorio de la sesión {instance.id} han sido eliminados." + RESET_COLOR)
    
def delete_video_instance(video_evidence):
    if os.path.exists(video_evidence.video_file.path):
        os.remove(video_evidence.video_file.path)
    video_evidence.delete()
    print(GREEN_COLOR + f"Video eliminado" + RESET_COLOR)

@receiver(post_save, sender=VideoEvidence)
def schedule_video_deletion(sender, instance, **kwargs):
    Timer(DELETE_DELAY, delete_video_instance, [instance]).start()
    print(RED_COLOR + f"Video {instance.id} programado para eliminarse en {DELETE_DELAY} segundos" + RESET_COLOR)