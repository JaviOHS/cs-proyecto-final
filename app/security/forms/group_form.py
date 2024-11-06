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
