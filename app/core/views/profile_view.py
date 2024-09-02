from urllib import request
from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from app.core.forms.perfil import UserProfileForm, UserProfilePasswordForm
from app.core.models import UserProfile
from django.contrib import messages
from django.contrib.auth import logout


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'components/profile.html'
    title1 = 'Perfil'
    title2 = 'Tu Perfil'
    login_url = reverse_lazy('login')  # Redirect to login page if not authenticated

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(self.login_url)

        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['user_profile'] = UserProfile.objects.get(user=self.request.user)
        except UserProfile.DoesNotExist:
            # Handle the case where UserProfile doesn't exist
            context['user_profile'] = None
        context['profile'] = getattr(self.request.user, 'userprofile', None)
        context['title1'] = self.title1
        context['title2'] = self.title2
        return context

    
class UserProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'components/profile_update.html'
    success_url = reverse_lazy('core:profile')

    def get_object(self):
        return self.request.user.userprofile
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        password_form = UserProfilePasswordForm(request.user, request.POST)
        
        if 'password_change' in request.POST:
            if password_form.is_valid():
                password_form.save()
                messages.success(request, 'Contraseña actualizada con éxito. Por favor, inicia sesión de nuevo.')
                logout(request)
                return redirect('security:signin')  # Use the correct URL name
        elif form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        
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