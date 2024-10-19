from django import forms
from app.monitoring.models import MonitoringSession
from django.core.exceptions import ValidationError

class MonitoringSessionForm(forms.ModelForm):
    class Meta:
        model = MonitoringSession
        fields = ['name', 'description', 'detection_model']
        error_messages = {
            'unique': {
                'name': 'Ya existe una sesión con este nombre. Por favor, elija otro.',
                'detection_model': 'Ya existe una sesión con este modelo de detección. Por favor, elija otro.',
            }
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'id_name',
                'class': 'inputs',
                'placeholder': 'Nombre de la sesión',
                'autofocus': True
            }),
            'description': forms.Textarea(attrs={
                'id': 'id_description',
                'class': 'textarea',
                'rows': 2,
                'placeholder': 'Descripción de la sesión'
            }),
            'detection_model': forms.RadioSelect(attrs={
                'class': 'checkbox custom-checkbox-class',
                'id': 'id_detection_model'
            })
        }

    def __init__(self, *args, **kwargs):
        detection_model = kwargs.pop('detection_model')
        super().__init__(*args, **kwargs)
        self.fields['detection_model'].queryset = detection_model

    def clean(self):
        cleaned_data = super().clean()
        user = self.initial.get('user')  # Asume que el usuario se pasa como contexto inicial

        detection_model = cleaned_data.get('detection_model')
        if user and detection_model:
            existing_session = MonitoringSession.objects.filter(user=user, detection_model=detection_model).exists()
            if existing_session:
                raise ValidationError("Ya existe una sesión de monitoreo para este modelo de detección y este usuario.")
        
        return cleaned_data

    def clean_name(self):
        name = self.cleaned_data['name']
        return name.title()
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip() 
        if not description: return description 
        if description[-1] != '.': description += '.'
        return description.capitalize()
