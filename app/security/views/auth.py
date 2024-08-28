from django.shortcuts import redirect, render
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import FormView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from app.security.forms.auth import CustomUserCreationForm
from django.contrib.auth.forms import AuthenticationForm

class SignoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "Has cerrado sesión exitosamente.")
        return redirect("home")

class SignupView(FormView):
    form_class = CustomUserCreationForm
    template_name = "security/auth/signup.html"
    success_url = reverse_lazy("security:signin")
    extra_context = {"title1": "Registro", "title2": "Registro de Usuarios"}
    
    def form_valid(self, form):
        user = form.save()
        username = form.cleaned_data.get('username')
        messages.success(self.request, f"Bienvenido {username}, tu cuenta ha sido creada exitosamente. Inicia sesión para continuar.")
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Error al registrar el usuario. Por favor, revisa los datos ingresados.")
        return super().form_invalid(form)

class SigninView(FormView):
    form_class = AuthenticationForm
    template_name = "security/auth/signin.html"
    extra_context = {"title1": "Login", "title2": "Inicio de Sesión"}

    def form_valid(self, form):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(self.request, username=username, password=password)
        
        if user is not None:
            login(self.request, user)
            messages.success(self.request, "Has iniciado sesión correctamente.")
            return redirect("home")
        else:
            messages.error(self.request, "El usuario o la contraseña son incorrectos")
            return self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['success_messages'] = messages.get_messages(self.request)
        return context
