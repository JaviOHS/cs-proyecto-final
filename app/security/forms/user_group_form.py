from django import forms
from app.security.models import User

class UserGroupForm (forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'groups']
        widgets = {
            'groups': forms.CheckboxSelectMultiple(attrs={
                'id': 'id_groups',
                }
            ),
            'username': forms.TextInput(attrs={
                'id': 'id_username',
                'class': 'inputs',
                'placeholder': 'Nombre de usuario',
                'autofocus': True
                }
            ),
            'first_name': forms.TextInput(attrs={
                'id': 'id_first_name',
                'class': 'inputs',
                'placeholder': 'Nombre'
                }
            ),
            'last_name': forms.TextInput(attrs={
                'id': 'id_last_name',
                'class': 'inputs',
                'placeholder': 'Apellido'
                }
            )
        }