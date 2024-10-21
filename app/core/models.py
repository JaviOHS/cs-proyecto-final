from django.db import models
from django.contrib.auth.models import User
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class User2FAPreferences(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='two_fa_preferences')
    is_2fa_enabled = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - 2FA {'Enabled' if self.is_2fa_enabled else 'Disabled'}"