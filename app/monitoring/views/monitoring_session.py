from app.threat_management.models import Detection
from app.monitoring.models import MonitoringSession
from app.monitoring.forms.monitoring_session import MonitoringSessionForm
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView
from app.core.views.confirm_delete import ConfirmDeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin

class MonitoringSessionView(ListView, LoginRequiredMixin):
    model = MonitoringSession
    template_name = 'monitoring/monitoring_session.html'
    context_object_name = 'monitoring_sessions'

    def get_queryset(self):
        return MonitoringSession.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Monitoreo"
        context["title2"] = "Sesiones de Monitoreo"
        return context

class CreateMonitoringSessionView(CreateView):
    model = MonitoringSession
    form_class = MonitoringSessionForm
    template_name = 'monitoring/form_session.html'
    success_url = reverse_lazy('monitoring:monitoring_session')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['detection_models'] = Detection.objects.filter(is_active=True)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Crear Registros"
        context["title2"] = "Crear Sesión de Monitoreo"
        context["back_url"] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        form.instance.detection_models.set(form.cleaned_data['detection_models'])
        form.instance.save()
        monitoring = self.object
        messages.success(self.request, f"Éxito al crear la sesión {monitoring.id}.")
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Revise los campos.')
        
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{form[field].label} - {error}")
        
        return super().form_invalid(form)

    def get_success_url(self):
        return self.success_url

class UpdateMonitoringSessionView(UpdateView):
    model = MonitoringSession
    form_class = MonitoringSessionForm
    template_name = 'monitoring/form_session.html'
    context_object_name = 'session'
    success_url = reverse_lazy('monitoring:monitoring_session')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['detection_models'] = Detection.objects.filter(is_active=True)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Actualizar Registros"
        context["title2"] = "Actualizar Sesión de Monitoreo"
        context["back_url"] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        self.object.detection_models.set(form.cleaned_data['detection_models'])
        monitoring = self.object
        messages.success(self.request, f"Éxito al actualizar la sesión {monitoring.id}.")
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Revise los campos marcados en rojo.')
        return super().form_invalid(form)
    
class DeleteMonitoringSessionView(ConfirmDeleteView):
    model = MonitoringSession
    success_url = reverse_lazy('monitoring:monitoring_session')

    def get_details(self):
        """Personaliza los detalles que se muestran en la confirmación."""
        return f"ID: {self.object.id} - {self.object.name}"
