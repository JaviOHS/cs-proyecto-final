from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from app.security.forms.auth import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _  # Para traducir las variables dinámicas
from app.security.mixins.authentication_mixin import AuthErrorHandlingMixin
import random
from django.core.mail import send_mail
from django.contrib.auth import authenticate

class SignoutView(AuthErrorHandlingMixin, LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "Has cerrado sesión exitosamente.")
        return redirect("home")

class SignupView(AuthErrorHandlingMixin, FormView):
    form_class = CustomUserCreationForm
    template_name = "signup.html"
    success_url = reverse_lazy("security:verify_signup_2fa")
    extra_context = {"title1": _("Registro"), "title2": _("Registro de Usuarios")}
    redirect_authenticated_user = True
    
    def form_valid(self, form):
        user = form.save(commit=False)
        
        # Generate a 6-digit code
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Store the code and user data in session
        self.request.session['signup_2fa_code'] = code
        self.request.session['signup_user_data'] = form.cleaned_data
        
        # Send the code via email
        send_mail(
            'Your 2FA Code for Registration',
            f'Your 2FA code for registration is: {code}',
            'from@example.com',
            [user.email],
            fail_silently=False,
        )
        
        messages.success(self.request, f"Se ha enviado un código de verificación a {user.email}. Por favor, verifícalo para completar el registro.")
        return super().form_valid(form)

class SigninView(AuthErrorHandlingMixin, FormView):
    form_class = AuthenticationForm
    template_name = "signin.html"
    extra_context = {"title1": "Login", "title2": _("Inicio de Sesión")}
    redirect_authenticated_user = True

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)

        if user is not None:
            # Generate a 6-digit code
            code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
            
            # Store the code in session
            self.request.session['2fa_code'] = code
            self.request.session['user_id'] = user.id

            # Send the code via email
            send_mail(
                'Your 2FA Code',
                f'Your 2FA code is: {code}',
                'from@example.com',
                [user.email],
                fail_silently=False,
            )

            # Redirect to 2FA verification page
            return redirect('security:verify_2fa')
        else:
            messages.error(self.request, "El usuario o la contraseña son incorrectos.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['success_messages'] = messages.get_messages(self.request)
        return context