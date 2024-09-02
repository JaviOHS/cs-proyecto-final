from django import forms
from app.core.models import UserProfile
from django.contrib.auth.forms import PasswordChangeForm

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'dni', 'phone', 'image']

class UserProfilePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Quitar los estilos personalizados
        for field in self.fields.values():
            field.widget.attrs.pop('class', None)
