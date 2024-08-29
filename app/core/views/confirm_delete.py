from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.contrib import messages

class ConfirmDeleteView(DeleteView):
    template_name = 'components/confirm_delete.html'  # Plantilla genérica
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied("No tienes permiso para eliminar este objeto.")
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Eliminar Registros"
        context["title2"] = f"Eliminar {self.model._meta.verbose_name}"
        context["details"] = self.get_details()
        context["confirm_url"] = self.get_confirm_url()
        context["cancel_url"] = self.get_cancel_url()
        return context

    def get_details(self):
        """Método para proporcionar detalles específicos del objeto que se va a eliminar."""
        return str(self.object)

    def get_confirm_url(self):
        """Método para obtener la URL de confirmación del formulario de eliminación."""
        return self.request.path

    def get_cancel_url(self):
        """Método para obtener la URL de cancelación."""
        return self.success_url

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, f"{self.model._meta.verbose_name} eliminado con éxito.")
        return super().delete(request, *args, **kwargs)
