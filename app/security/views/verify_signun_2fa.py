from django.views.generic import FormView
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django import forms
from app.security.forms.auth import CustomUserCreationForm

class VerifySignup2FAForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6)

class VerifySignup2FAView(FormView):
    form_class = VerifySignup2FAForm
    template_name = "verify_signup_2fa.html"
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        entered_code = form.cleaned_data['code']
        stored_code = self.request.session.get('signup_2fa_code')
        user_data = self.request.session.get('signup_user_data')

        if entered_code == stored_code and user_data:
            # Create and save the user
            user_form = CustomUserCreationForm(user_data)
            if user_form.is_valid():
                user = user_form.save()
                login(self.request, user)
                messages.success(self.request, f"Bienvenido {user.username}, tu cuenta ha sido creada exitosamente.")
                
                # Clear session data
                del self.request.session['signup_2fa_code']
                del self.request.session['signup_user_data']
                
                return super().form_valid(form)
            else:
                messages.error(self.request, "Hubo un error al crear tu cuenta. Por favor, intenta nuevamente.")
                return redirect('security:signup')
        else:
            messages.error(self.request, "Código incorrecto. Por favor, inténtalo de nuevo.")
            return self.form_invalid(form)