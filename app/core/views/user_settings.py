from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from app.core.models import User2FAPreferences
from django.utils.translation import gettext_lazy as _

class UserSettingsView(LoginRequiredMixin, UpdateView):
    model = User2FAPreferences
    fields = ['is_2fa_enabled', 'is_facial_recognition_enabled']
    template_name = 'user_settings.html'

    def get_object(self, queryset=None):
        return User2FAPreferences.objects.get_or_create(user=self.request.user)[0]

    def get_success_url(self):
        return reverse('core:user_settings')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages_list = []
        
        # Check 2FA changes
        if self.object.is_2fa_enabled:
            messages_list.append("Se ha habilitado la verificación de dos factores (2FA) para su cuenta.")
        else:
            messages_list.append("Se ha deshabilitado la verificación de dos factores (2FA) para su cuenta.")
            
        # Check facial recognition changes
        if self.object.is_facial_recognition_enabled:
            messages_list.append("Se ha habilitado el reconocimiento facial para su cuenta.")
        else:
            messages_list.append("Se ha deshabilitado el reconocimiento facial para su cuenta.")
        
        for message in messages_list:
            messages.success(self.request, message)
            
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title1'] = _("Configuraciones")
        context['title2'] = _("Configuraciones de Seguridad")
        return context