from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib import messages
from app.core.forms.perfil import UserProfileForm, UserProfilePasswordForm
from django.contrib.auth import get_user_model

User = get_user_model()

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'components/profile.html'
    title1 = 'Perfil'
    title2 = 'Tu Perfil'
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
    template_name = 'components/profile_update.html'
    success_url = reverse_lazy('core:profile')

    def get_object(self):
        return self.request.user

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
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
            if form.is_valid():
                return self.form_valid(form)
            else:
                return self.form_invalid(form)
        
        return self.render_to_response(self.get_context_data(form=form, password_form=password_form))
        
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Perfil actualizado con éxito.')
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = self.get_object()
        context['password_form'] = UserProfilePasswordForm(self.request.user)
        context['title1'] = 'Actualizar Perfil'
        context['title2'] = 'Actualiza tu información'
        return context
