from django.forms import ValidationError
from django.views.generic import ListView
from app.alarm.models import Alarm
from app.alarm.forms.alarm import AlarmForm
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from app.core.views.confirm_delete import ConfirmDeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

class AlarmListView(LoginRequiredMixin, ListView):
    model = Alarm
    template_name = 'alarm_list.html'
    context_object_name = 'alarm_models'
    
    def get_queryset(self):
        return Alarm.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Gestión de Alarmas"
        context["title2"] = "Modelos de Alarmas"
        return context
    
class AlarmCreateView(LoginRequiredMixin, CreateView):
    model = Alarm
    template_name = 'alarm_form.html'
    form_class = AlarmForm
    success_url = reverse_lazy('alarm:alarm_list')
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para realizar esta acción.')
        return redirect('alarm:alarm_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Crear Registros"
        context["title2"] = "Crear Alarmas Personalizadas"
        context["back_url"] = self.success_url
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        response = super().form_valid(form)
        alarm = self.object
        messages.success(self.request, f"Éxito al crear alarma para el modelo {alarm.detection}.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Revise los campos.')

        for field, errors in form.errors.items():
            if field != '__all__':
                for error in errors:
                    messages.error(self.request, f"{form.fields[field].label} - {error}")
            else:
                for error in errors:
                    messages.error(self.request, f"Error - {error}")

        return super().form_invalid(form)
    
class AlarmUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Alarm
    template_name = 'alarm_form.html'
    form_class = AlarmForm
    success_url = reverse_lazy('alarm:alarm_list')
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para realizar esta acción.')
        return redirect('alarm:alarm_list')
    
    def test_func(self):
        session = self.get_object()
        return session.user == self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Actualizar Registros"
        context["title2"] = "Actualizar Alarmas Personalizadas"
        context["back_url"] = self.success_url
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        alarm = self.object
        messages.success(self.request, f"Éxito al actualizar alarma para el modelo {alarm.detection}.")
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Revise los campos.')

        for field, errors in form.errors.items():
            if field != '__all__':
                for error in errors:
                    messages.error(self.request, f"{form.fields[field].label} - {error}")
            else:
                for error in errors:
                    messages.error(self.request, f"Error - {error}")

        return super().form_invalid(form)
    
class AlarmDeleteView(LoginRequiredMixin, UserPassesTestMixin, ConfirmDeleteView):
    model = Alarm
    success_url = reverse_lazy('alarm:alarm_list')
    
    def test_func(self):
        session = self.get_object()
        return session.user == self.request.user
    
    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para realizar esta acción.')
        return redirect('alarm:alarm_list')
    
    def get_details(self):
        """Personaliza los detalles que se muestran en la confirmación."""
        return f"ID: {self.object.id} - {self.object.detection}"
