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
                'class': 'bg-white text-gray-900 text-lg rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5 dark:bg-primary-dark dark:placeholder-gray-400 dark:text-gray-200 dark:focus:ring-blue-500 dark:focus:border-blue-500',
                'placeholder': 'Ingrese Amenaza'
            }),
            'description': forms.Textarea(attrs={
                'id': 'id_description',
                'class': 'bg-white text-gray-900 text-lg rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-3 p-2.5 dark:bg-primary-dark dark:placeholder-gray-400 dark:text-gray-200 dark:focus:ring-blue-500 dark:focus:border-blue-500',
                'rows': 2,
                'placeholder': 'Descripción de Amenaza'
            }),
            'icon': forms.TextInput(attrs={
                'id': 'id_icon',
                'class': 'bg-white text-gray-900 text-lg rounded-lg focus:ring-blue-500 focus:border-blue-500 block w-full pl-10 p-2.5 dark:bg-primary-dark dark:placeholder-gray-400 dark:text-gray-200 dark:focus:ring-blue-500 dark:focus:border-blue-500',
                'placeholder': 'Ícono de Font Awesome'
            })
        }
        
    def clean_name(self):
        name = self.cleaned_data['name']
        return name.upper()