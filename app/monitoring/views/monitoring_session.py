from app.threat_management.models import Detection
from app.monitoring.models import MonitoringSession
from app.monitoring.forms.monitoring_session import MonitoringSessionForm
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView
from app.core.views.confirm_delete import ConfirmDeleteView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from app.security.mixins.permission_mixin import UserPermissionMixin
from app.security.mixins.form_error_handling import FormErrorHandlingMixin

class MonitoringSessionView(UserPermissionMixin, ListView):
    model = MonitoringSession
    template_name = 'monitoring_session.html'
    context_object_name = 'monitoring_sessions'
    permission_required = 'view_monitoringsession'

    def get_queryset(self):
        return MonitoringSession.objects.filter(user=self.request.user).order_by('id')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Monitoreo")
        context["title2"] = _("Sesiones de Monitoreo")
        return context

class CreateMonitoringSessionView(FormErrorHandlingMixin, UserPermissionMixin, CreateView):
    model = MonitoringSession
    form_class = MonitoringSessionForm
    template_name = 'form_session.html'
    success_url = reverse_lazy('monitoring:monitoring_session')
    permission_required = 'add_monitoringsession'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['detection_model'] = Detection.objects.filter(is_active=True)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Crear Registros")
        context["title2"] = _("Crear Sesión de Monitoreo")
        context["back_url"] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def add_success_message(self):
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'detection_model') and self.object.detection_model:
            messages.success(self.request, f"Éxito al crear la sesión para la detección {self.object.detection_model.name}.")
        else:
            messages.success(self.request, "Éxito al crear la sesión.")

class UpdateMonitoringSessionView(FormErrorHandlingMixin, UserPermissionMixin, UpdateView):
    model = MonitoringSession
    form_class = MonitoringSessionForm
    template_name = 'form_session.html'
    context_object_name = 'session'
    success_url = reverse_lazy('monitoring:monitoring_session')
    permission_required = 'change_monitoringsession'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['detection_model'] = Detection.objects.filter(is_active=True)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Actualizar Registros")
        context["title2"] = _("Actualizar Sesión de Monitoreo")
        context["back_url"] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def add_success_message(self):
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'detection_model') and self.object.detection_model:
            messages.success(self.request, f"Éxito al actualizar la sesión para la detección {self.object.detection_model.name}.")
        else:
            messages.success(self.request, "Éxito al actualizar la sesión.")
    
class DeleteMonitoringSessionView(FormErrorHandlingMixin, UserPermissionMixin, ConfirmDeleteView):
    model = MonitoringSession
    success_url = reverse_lazy('monitoring:monitoring_session')
    permission_required = 'delete_monitoringsession'
    
    def get_details(self):
        return f"ID: {self.object.id} - {self.object.name}"

    def add_success_message(self):
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'detection_model') and self.object.detection_model:
            messages.success(self.request, f"Éxito al eliminar la sesión para la detección: {self.object.detection_model.name}.")
        else:
            messages.success(self.request, "Éxito al eliminar la sesión.")