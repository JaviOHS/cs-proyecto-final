from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from app.core.models import User2FA
from app.security.forms.auth import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from app.security.mixins.authentication_mixin import AuthErrorHandlingMixin
import random
from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

class ExtendSessionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        request.session.modified = True
        return JsonResponse({'status': 'success'})

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
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        session_data = {}
        for key, value in form.cleaned_data.items():
            if key == 'image' and value:
                path = default_storage.save(
                    f'temp/signup_{form.cleaned_data["username"]}_{value.name}',
                    ContentFile(value.read())
                )
                session_data['image_path'] = path
            elif key not in ['password1', 'password2']:
                session_data[key] = value
                
        session_data['password'] = form.cleaned_data['password1']
        
        self.request.session['signup_2fa_code'] = code
        self.request.session['signup_user_data'] = session_data
        
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
            two_fa_preferences, created = User2FA.objects.get_or_create(user=user)
            
            if two_fa_preferences.is_2fa_enabled:
                code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
                self.request.session['2fa_code'] = code
                self.request.session['user_id'] = user.id

                send_mail(
                    'Your 2FA Code',
                    f'Your 2FA code is: {code}',
                    'from@example.com',
                    [user.email],
                    fail_silently=False,
                )

                return redirect('security:verify_2fa')
            else:
                login(self.request, user)
                messages.success(self.request, "Has iniciado sesión correctamente.")
                return redirect("home")
        else:
            messages.error(self.request, "El usuario o la contraseña son incorrectos.")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        show_facial_recognition = User2FA.objects.filter(
            is_facial_recognition_enabled=True
        ).exists()
        
        context.update({
            'show_facial_recognition': show_facial_recognition,
            'success_messages': messages.get_messages(self.request)
        })
        return context