from django import forms
from django.contrib.auth.forms import UserCreationForm
from app.security.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'dni', 'phone', 'image')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Usuario'
        self.fields['password2'].label = 'Confirmar Contraseña'
        
    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        return first_name.title()
    
    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        return last_name.title()
    
    def clean_email(self):
        email = self.cleaned_data['email']
        return email.lower()
