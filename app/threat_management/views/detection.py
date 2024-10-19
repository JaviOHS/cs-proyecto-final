from django.views.generic import ListView
from app.threat_management.models import Detection
from app.threat_management.forms.detection import DetectionForm
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from app.core.views.confirm_delete import ConfirmDeleteView
from django.utils.translation import gettext_lazy as _
from app.security.mixins.permission_mixin import UserPermissionMixin
from app.security.mixins.form_error_handling import FormErrorHandlingMixin

class DetectionListView(UserPermissionMixin, ListView):
    model = Detection
    template_name = 'detection_list.html'
    context_object_name = 'detection_models'
    permission_required = 'view_detection'
    
    def get_queryset(self):
        return Detection.objects.filter(is_active=True).order_by('id')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Gestión de Amenazas")
        context["title2"] = _("Modelos de Detección de Amenazas")
        return context
    
class DetectionCreateView(FormErrorHandlingMixin, UserPermissionMixin, CreateView):
    model = Detection
    template_name = 'detection_form.html'
    form_class = DetectionForm
    success_url = reverse_lazy('detection:detection_list')
    permission_required = 'add_detection'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Crear Registros")
        context["title2"] = _("Crear Modelo de Detección de Amenaza")
        context["back_url"] = self.success_url
        return context

    def add_success_message(self):
        if hasattr(self, 'object') and self.object:
            messages.success(self.request, f"Éxito al crear el modelo de amenaza {self.object.name}.")
        else:
            messages.success(self.request, "Éxito al crear el modelo de amenaza.")

class DetectionUpdateView(FormErrorHandlingMixin, UserPermissionMixin, UpdateView):
    model = Detection
    template_name = 'detection_form.html'
    form_class = DetectionForm
    success_url = reverse_lazy('detection:detection_list')
    permission_required = 'change_detection'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Actualizar Registros")
        context["title2"] = _("Actualizar Modelo de Detección de Amenaza")
        context["back_url"] = self.success_url
        return context
    
    def add_success_message(self):
        if hasattr(self, 'object') and self.object:
            messages.success(self.request, f"Éxito al actualizar el modelo de amenaza {self.object.name}.")
        else:
            messages.success(self.request, "Éxito al actualizar el modelo de amenaza.")

class DetectionDeleteView(FormErrorHandlingMixin, UserPermissionMixin, ConfirmDeleteView):
    model = Detection
    success_url = reverse_lazy('detection:detection_list')
    permission_required = 'delete_detection'

    def get_details(self):
        """Personaliza los detalles que se muestran en la confirmación."""
        return f"ID: {self.object.id} - {self.object.name}"

    def add_success_message(self):
        if hasattr(self, 'object') and self.object:
            messages.success(self.request, f"Éxito al eliminar el modelo de amenaza: {self.object.name}.")
        else:
            messages.success(self.request, "Éxito al eliminar el modelo de amenaza.")