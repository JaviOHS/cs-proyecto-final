from django.views.generic import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.contrib import messages
from app.core.models import User2FAPreferences
from django.utils.translation import gettext_lazy as _

class UserSettingsView(LoginRequiredMixin, UpdateView):
    model = User2FAPreferences
    fields = ['is_2fa_enabled']
    template_name = 'user_settings.html'

    def get_object(self, queryset=None):
        return User2FAPreferences.objects.get_or_create(user=self.request.user)[0]

    def get_success_url(self):
        return reverse('core:user_settings')

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object.is_2fa_enabled:
            messages.success(self.request, "Se a habilitado la verificación de dos factores 2FA para su cuenta.")
        else:
            messages.success(self.request, "Se a deshabilitado la verificación de dos factores 2FA para su cuenta.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title1'] = _("Configuraciones")
        context['title2'] = _("Configuraciones de Seguridad")
        return context