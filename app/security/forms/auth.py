from django import forms
from django.contrib.auth.forms import UserCreationForm
from app.security.models import User
from app.security.utils import validate_image, resize_image

class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'dni', 'phone', 'image')
    
    def clean_first_name(self):
        first_name = self.cleaned_data['first_name']
        return first_name.title()
    
    def clean_last_name(self):
        last_name = self.cleaned_data['last_name']
        return last_name.title()
    
    def clean_email(self):
        email = self.cleaned_data['email']
        return email.lower()
    
    def clean_image(self):
        image = self.cleaned_data.get('image', None) 
        
        if image and hasattr(image, 'path'):
            validate_image(image)
            resize_image(image.path, (300, 300))
        
        return image
    