from django import forms
from app.threat_management.models import Detection

class DetectionForm(forms.ModelForm):
    class Meta:
        model = Detection
        fields = ['name', 'description', 'icon']
        error_messages = {
            'unique': {
                'name': 'Ya existe una amenaza con este nombre. Por favor, elija otro.'
            }
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'id_name',
                'class': 'inputs',
                'placeholder': 'Ingrese Amenaza'
            }),
            'description': forms.Textarea(attrs={
                'id': 'id_description',
                'class': 'textarea',
                'rows': 2,
                'placeholder': 'Descripción de Amenaza'
            }),
            'icon': forms.TextInput(attrs={
                'id': 'id_icon',
                'class': 'inputs',
                'placeholder': 'Ícono de Font Awesome'
            })
        }
        
    def clean_name(self):
        name = self.cleaned_data['name']
        return name.title()
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip() 
        if not description: return description 
        if description[-1] != '.': description += '.'
        return description.capitalize()