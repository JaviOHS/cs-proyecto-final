from django.views.generic import FormView
from django.shortcuts import redirect
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django import forms
from app.security.forms.auth import CustomUserCreationForm
from app.security.models import User
from django.core.files.storage import default_storage
from django.core.files import File

class Verify2FAForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6)
    
class Verify2FAView(FormView):
    form_class = Verify2FAForm
    template_name = "verify_2fa.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_signup'] = False
        return context

    def form_valid(self, form):
        entered_code = form.cleaned_data['code']
        stored_code = self.request.session.get('2fa_code')
        user_id = self.request.session.get('user_id')

        if entered_code == stored_code and user_id:
            user = User.objects.get(id=user_id)
            login(self.request, user)
            messages.success(self.request, "Has iniciado sesión correctamente.")
            del self.request.session['2fa_code']
            del self.request.session['user_id']
            return super().form_valid(form)
        else:
            return self.form_invalid(form)
        
    def form_invalid(self, form):
        messages.error(self.request, "Código incorrecto. Por favor, inténtalo de nuevo.")
        return super().form_invalid(form)

class VerifySignup2FAView(FormView):
    form_class = Verify2FAForm
    template_name = "verify_2fa.html"
    success_url = reverse_lazy("home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_signup'] = True
        return context

    def form_valid(self, form):
        entered_code = form.cleaned_data['code']
        stored_code = self.request.session.get('signup_2fa_code')
        user_data = self.request.session.get('signup_user_data')

        if entered_code == stored_code and user_data:
            try:
                image_path = user_data.pop('image_path', None)
                
                user = User.objects.create_user(
                    username=user_data['username'],
                    email=user_data['email'],
                    password=user_data['password'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    dni=user_data['dni'],
                    phone=user_data['phone']
                )

                if image_path:
                    try:
                        with default_storage.open(image_path) as f:
                            user.image.save(
                                image_path.split('/')[-1],
                                File(f),
                                save=True
                            )
                        default_storage.delete(image_path)
                    except Exception as e:
                        messages.warning(self.request, "No se pudo procesar la imagen de perfil, pero tu cuenta fue creada.")

                login(self.request, user)
                messages.success(self.request, f"Bienvenido {user.username}, tu cuenta ha sido creada exitosamente.")
                
                del self.request.session['signup_2fa_code']
                del self.request.session['signup_user_data']
                
                return super().form_valid(form)
                
            except Exception as e:
                messages.error(self.request, "Hubo un error al crear tu cuenta. Por favor, intenta nuevamente.")
                return redirect('security:signup')
        else:
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, "Código incorrecto. Por favor, inténtalo de nuevo.")
        return super().form_invalid(form)
