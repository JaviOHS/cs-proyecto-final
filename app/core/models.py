from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class User2FA(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_fa_preferences')
    is_2fa_enabled = models.BooleanField(default=False)
    is_facial_recognition_enabled = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Preferencia de 2FA"
        verbose_name_plural = "Preferencias de 2FA"

    def __str__(self):
        return f"{self.user.username} - 2FA: {'Enabled' if self.is_2fa_enabled else 'Disabled'}, Face Recognition: {'Enabled' if self.is_facial_recognition_enabled else 'Disabled'}"