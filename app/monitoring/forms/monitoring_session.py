from django import forms
from app.monitoring.models import MonitoringSession

class MonitoringSessionForm(forms.ModelForm):
    detection_models = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple(
            attrs={
                'class': 'dark:text-gray-300',
            }
        ),
        error_messages={'required': 'Por favor, seleccione al menos un modelo.'}
    )   

    class Meta:
        model = MonitoringSession
        fields = ['name', 'description', 'detection_models']
        error_messages = {
            'unique': {
                'name': 'Ya existe una sesión con este nombre. Por favor, elija otro.'
            }
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'id_name',
                'class': 'inputs',
                'placeholder': 'Nombre de la sesión'
            }),
            'description': forms.Textarea(attrs={
                'id': 'id_description',
                'class': 'textarea',
                'rows': 2,
                'placeholder': 'Descripción de la sesión'
            }),
        }
    def __init__(self, *args, **kwargs):
        detection_models = kwargs.pop('detection_models')
        super().__init__(*args, **kwargs)
        self.fields['detection_models'].queryset = detection_models
    
    def clean_name(self):
        name = self.cleaned_data['name']
        return name.title()
    
    def clean_description(self):
        description = self.cleaned_data['description']
        if description[-1] != '.': description += '.'
        return description.capitalize()
