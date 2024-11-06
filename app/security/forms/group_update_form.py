from django import forms
from django.contrib.auth.models import Group, Permission

class GroupUpdateForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple
    )
    
    class Meta:
        model = Group
        fields = ['name', 'permissions']
        widgets = {
            'name': forms.TextInput(attrs={
                'id': 'id_name',
                'class': 'inputs',
                'placeholder': 'Nombre del Grupo',
                'autofocus': True,
            }),
        }
