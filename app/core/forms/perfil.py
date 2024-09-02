from django import forms
from app.core.models import UserProfile
from django.contrib.auth.forms import PasswordChangeForm

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['first_name', 'last_name', 'email', 'dni', 'phone', 'image']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full py-2 px-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full py-2 px-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full py-2 px-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
            'dni': forms.TextInput(attrs={
                'class': 'w-full py-2 px-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full py-2 px-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
        }

class UserProfilePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full py-2 px-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-indigo-500'
            })
