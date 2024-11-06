from django import forms
from django.contrib.auth.models import Group, Permission

class GroupForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        error_messages = {
            'unique': {
                'name': 'Ya existe un grupo con este nombre. Por favor, elija otro.',
            }
        }
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'id_name',
                'class': 'inputs',
                'placeholder': 'Nombre del Grupo',
                'autofocus': True,
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super(GroupForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['permissions'].initial = self.instance.permissions.all()
    
    def clean_name(self):
        name = self.cleaned_data['name']
        return name.title()