from django.forms import ValidationError
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from app.alarm.models import Alarm
from app.alarm.forms.alarm import AlarmForm
from app.core.views.confirm_delete import ConfirmDeleteView
from django.utils.translation import gettext_lazy as _
from app.security.mixins.permission_mixin import UserPermissionMixin
from django.contrib import messages
from app.security.mixins.form_error_handling import FormErrorHandlingMixin
from app.threat_management.models import Detection  

class AlarmListView(UserPermissionMixin, ListView):
    model = Alarm
    template_name = 'alarm_list.html'
    context_object_name = 'alarm_models'
    permission_required = 'view_alarm'

    def get_queryset(self):
        return Alarm.objects.filter(user=self.request.user).order_by('id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Gestión de Alarmas")
        context["title2"] = _("Modelos de Alarmas")
        return context

class AlarmCreateView(FormErrorHandlingMixin, UserPermissionMixin, CreateView):
    model = Alarm
    template_name = 'alarm_form.html'
    form_class = AlarmForm
    success_url = reverse_lazy('alarm:alarm_list')
    permission_required = 'add_alarm'
        
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['detection_model'] = Detection.objects.filter(is_active=True)
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Crear Registros")
        context["title2"] = _("Crear Alarmas Personalizadas")
        context["back_url"] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def add_success_message(self):
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'detection') and self.object.detection:
            messages.success(self.request, f"Éxito al crear alarma para el modelo {self.object.detection}.")
        else:
            messages.success(self.request, "Éxito al crear la alarma.")
    
class AlarmUpdateView(FormErrorHandlingMixin, UserPermissionMixin, UpdateView):
    model = Alarm
    template_name = 'alarm_form.html'
    form_class = AlarmForm
    success_url = reverse_lazy('alarm:alarm_list')
    permission_required = 'change_alarm'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['detection_model'] = Detection.objects.filter(is_active=True)
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Actualizar Registros")
        context["title2"] = _("Actualizar Alarmas Personalizadas")
        context["back_url"] = self.success_url
        if self.object.sound_file:
            context['current_sound_file'] = self.object.sound_file.name
        else:
            context['current_sound_file'] = None
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def add_success_message(self):
        if hasattr(self, 'object') and self.object and hasattr(self.object, 'detection') and self.object.detection:
            messages.success(self.request, f"Éxito al actualizar alarma para el modelo {self.object.detection}.")
        else:
            messages.success(self.request, "Éxito al actualizar la alarma.")

class AlarmDeleteView(FormErrorHandlingMixin, UserPermissionMixin, ConfirmDeleteView):
    model = Alarm
    success_url = reverse_lazy('alarm:alarm_list')
    permission_required = 'delete_alarm'

    def get_details(self):
        return f"ID: {self.object.id} - {self.object.detection}"
    
    def add_success_message(self):
        messages.success(self.request, "Éxito al eliminar la alarma.")
