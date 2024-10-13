from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib import messages
from app.core.forms.profile_view import UserProfileForm, UserProfilePasswordForm
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _ # Para traducir las variables dinámicas

User = get_user_model()

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile.html'
    title1 = _('Perfil')
    title2 = _('Tu Perfil')
    login_url = reverse_lazy('login')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = self.request.user
        context['title1'] = self.title1
        context['title2'] = self.title2
        return context
    
class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = User 
    form_class = UserProfileForm
    template_name = 'profile_update.html'
    success_url = reverse_lazy('core:profile')

    def get_object(self):
        return self.request.user

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Aquí es donde pasamos request.FILES
        form = self.get_form()
        password_form = UserProfilePasswordForm(request.user, request.POST)

        if 'password_change' in request.POST:
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Contraseña actualizada con éxito. Por favor, inicia sesión de nuevo.')
                logout(request)
                return redirect('security:signin')
            else:
                return self.render_to_response(self.get_context_data(form=form, password_form=password_form))

        elif 'profile_update' in request.POST:
            # Pasa request.FILES al formulario
            form = self.form_class(request.POST, request.FILES, instance=self.object)  # Actualizado aquí
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)

        return self.render_to_response(self.get_context_data(form=form, password_form=password_form))

    def form_valid(self, form):
        if 'image' in self.request.FILES:
            form.instance.image = self.request.FILES['image']
            print(f"Archivo subido: {form.instance.image}")
        response = super().form_valid(form)
        return response


    def form_invalid(self, form):
        response = super().form_invalid(form)
        for field in form.errors:
            messages.error(self.request, f'{field}: {form.errors[field][0]}')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = self.get_object()
        context['password_form'] = UserProfilePasswordForm(self.request.user)
        context['title1'] = _('Actualizar Perfil')
        context['title2'] = _('Actualiza tu información')
        return context
