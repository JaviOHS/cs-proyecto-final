import os
from django.db.models.signals import post_save
from django.dispatch import receiver
from threading import Timer
from .models import VideoEvidence

DELETE_DELAY = 15 * 60

def delete_video_instance(video_evidence):
    if os.path.exists(video_evidence.video_file.path):
        os.remove(video_evidence.video_file.path)
    video_evidence.delete()

@receiver(post_save, sender=VideoEvidence)
def schedule_video_deletion(sender, instance, **kwargs):
    Timer(DELETE_DELAY, delete_video_instance, [instance]).start()
    print(f"Video {instance.id} scheduled for deletion in {DELETE_DELAY} seconds")
