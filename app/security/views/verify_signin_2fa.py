from django.views.generic import FormView
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django import forms

from app.security.models import User

class Verify2FAForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6)

class Verify2FAView(FormView):
    form_class = Verify2FAForm
    template_name = "verify_signin_2fa.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        entered_code = form.cleaned_data['code']
        stored_code = self.request.session.get('2fa_code')
        user_id = self.request.session.get('user_id')

        if entered_code == stored_code and user_id:
            user = User.objects.get(id=user_id)
            login(self.request, user)
            messages.success(self.request, "Has iniciado sesión correctamente.")
            
            # Clear session data
            del self.request.session['2fa_code']
            del self.request.session['user_id']
            
            return super().form_valid(form)
        else:
            messages.error(self.request, "Código incorrecto. Por favor, inténtalo de nuevo.")
            return self.form_invalid(form)