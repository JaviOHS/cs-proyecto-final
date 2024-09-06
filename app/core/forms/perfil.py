from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import get_user_model

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'dni', 'image']
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
            'phone': forms.TextInput(attrs={
                'class': 'w-full py-2 px-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
            'dni': forms.TextInput(attrs={
                'class': 'w-full py-2 px-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-indigo-500'
            }),
            'image': forms.ClearableFileInput(attrs={
                'class': 'w-full py-2 px-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-indigo-500',
                'accept': 'image/*'
            }),
        }

class UserProfilePasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'w-full py-2 px-4 border rounded-lg bg-gray-50 dark:bg-gray-800 dark:text-white focus:ring-2 focus:ring-indigo-500'
            })
