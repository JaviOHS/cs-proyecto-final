from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'dni', 'image', 'username']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'id': 'id_first_name',
                'class': 'inputs'
            }),
            'last_name': forms.TextInput(attrs={
                'id': 'id_last_name',
                'class': 'inputs'
            }),
            'email': forms.EmailInput(attrs={
                'id': 'id_email',
                'class': 'inputs'
            }),
            'phone': forms.TextInput(attrs={
                'id': 'id_phone',
                'class': 'inputs'
            }),
            'dni': forms.TextInput(attrs={
                'id': 'id_dni',
                'class': 'inputs',
                'readonly': 'readonly'
            }),
            'image': forms.FileInput(attrs={
                'id': 'id_image',
                'class': 'inputs',
                'accept': 'image/*'
            }),
            'username': forms.TextInput(attrs={
                'id': 'id_username',
                'class': 'inputs',
                'readonly': 'readonly'
            }),
        }

class UserProfilePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password2'].label = 'Confirmar Contraseña'
        for field in self.fields.values():
            field.widget.attrs.update({
                'id': 'id_password',
                'class': 'inputs',
            })

