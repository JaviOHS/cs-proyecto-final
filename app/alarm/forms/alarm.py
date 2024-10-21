from django import forms
from app.alarm.models import Alarm
from app.threat_management.models import Detection

class AlarmForm(forms.ModelForm):
    detection_model = forms.ModelChoiceField(
        queryset=Detection.objects.none(),
        widget=forms.RadioSelect(attrs={'id': 'id_detection_model'}),
        required=True,
        error_messages={
            'required': 'Debe seleccionar una amenaza.'
        }
    )

    class Meta:
        model = Alarm
        fields = ['detection_model', 'sound_file', 'notification_message']
        error_messages = {
            'unique': {
                'detection_model': 'Ya existe una alarma para esta amenaza. Por favor, elija otro.'
            }
        }
        widgets = {
            'sound_file': forms.FileInput(attrs={
                'id': 'dropzone-file',
                'class': 'hidden',
            }),
            'notification_message': forms.Textarea(attrs={
                'id': 'id_notification_message',
                'class': 'textarea',
                'placeholder': 'Escriba aquí el mensaje de notificación',
                'rows': 4,
                'autofocus': True 
            }),
        }
    
    def __init__(self, *args, **kwargs):
        detection_model = kwargs.pop('detection_model', None)
        super().__init__(*args, **kwargs)
        if detection_model is not None:
            self.fields['detection_model'].queryset = detection_model
        
        # Si estamos editando una alarma existente, seleccionamos el detection_model actual
        if self.instance.pk and self.instance.detection:
            self.initial['detection_model'] = self.instance.detection
    
    def clean_notification_message(self):
        notification_message = self.cleaned_data.get('notification_message', '').strip() 
        if not notification_message: return notification_message 
        if notification_message[-1] != '.': notification_message += '.'
        return notification_message.capitalize()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.detection = self.cleaned_data['detection_model']
        if commit:
            instance.save()
        return instance