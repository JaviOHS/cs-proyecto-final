from django import forms
from app.alarm.models import Alarm

class AlarmForm(forms.ModelForm):
    class Meta:
        model = Alarm
        fields = ['detection', 'sound_file', 'notification_message']
        error_messages = {
            'unique': {
                'detection': 'Ya existe una alarma para esta amenaza. Por favor, elija otro.'
            },
            'required': {
                'detection': 'Debe seleccionar una amenaza.'
            }
        }
        widgets = {
            'sound_file': forms.FileInput(attrs={
                'id': 'dropzone-file',
                'class': 'hidden',
            }),
            'detection': forms.RadioSelect(attrs={
                'id': 'id_detection',
                'class': 'checkbox custom-checkbox-class',
            }),
            'notification_message': forms.Textarea(attrs={
                'id': 'id_notification_message',
                'class': 'textarea',
                'placeholder': 'Escriba aquí el mensaje de notificación',
                'rows': 4,
                'autofocus': True 
            }),
        }
    
    def clean_notification_message(self):
        notification_message = self.cleaned_data.get('notification_message', '').strip() 
        if not notification_message: return notification_message 
        if notification_message[-1] != '.': notification_message += '.'
        return notification_message.capitalize()