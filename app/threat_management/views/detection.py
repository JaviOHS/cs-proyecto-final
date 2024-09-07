from django.views.generic import ListView
from app.threat_management.models import Detection
from app.threat_management.forms.detection import DetectionForm
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from app.core.views.confirm_delete import ConfirmDeleteView
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect

class DetectionListView(LoginRequiredMixin, ListView):
    model = Detection
    template_name = 'detection_list.html'
    context_object_name = 'detection_models'
    
    def get_queryset(self):
        return Detection.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Gestión de Amenazas"
        context["title2"] = "Modelos de Detección de Amenazas"
        return context
    
class DetectionCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Detection
    template_name = 'detection_form.html'
    form_class = DetectionForm
    success_url = reverse_lazy('detection:detection_list')
    
    def test_func(self):
        # Solo permitir acceso a administradores
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para realizar esta acción.')
        return redirect('detection:detection_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Crear Registros"
        context["title2"] = "Crear Modelo de Detección de Amenaza"
        context["back_url"] = self.success_url
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        detection = self.object
        messages.success(self.request, f"Éxito al crear el modelo de amenaza {detection.name}.")
        return response

    def form_invalid(self, form):
        messages.error(self.request, 'Revise los campos.')
        
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{form[field].label} - {error}")
        
        return super().form_invalid(form)
    
class DetectionUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Detection
    template_name = 'detection_form.html'
    form_class = DetectionForm
    success_url = reverse_lazy('detection:detection_list')
    
    def test_func(self):
        # Solo permitir acceso a administradores
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para realizar esta acción.')
        return redirect('detection:detection_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Actualizar Registros"
        context["title2"] = "Actualizar Modelo de Detección de Amenaza"
        context["back_url"] = self.success_url
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        detection = self.object
        messages.success(self.request, f"Éxito al actualizar el modelo de amenaza {detection.name}.")
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, 'Revise los campos.')
        
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{form[field].label} - {error}")
        
        return super().form_invalid(form)
    
class DetectionDeleteView(LoginRequiredMixin, UserPassesTestMixin, ConfirmDeleteView):
    model = Detection
    success_url = reverse_lazy('detection:detection_list')
    
    def test_func(self):
        # Solo permitir acceso a administradores
        return self.request.user.is_staff or self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, 'No tienes permisos para realizar esta acción.')
        return redirect('detection:detection_list')
    
    def get_details(self):
        """Personaliza los detalles que se muestran en la confirmación."""
        return f"ID: {self.object.id} - {self.object.name}"
