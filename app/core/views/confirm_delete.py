from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

class ConfirmDeleteView(DeleteView):
    template_name = 'confirm_delete.html' 
    success_url = reverse_lazy('home')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Eliminar Registros")
        context["title2"] = _(f"Eliminar {self.model._meta.verbose_name}")
        context["details"] = self.get_details()
        context["confirm_url"] = self.get_confirm_url()
        context["cancel_url"] = self.get_cancel_url()
        return context

    def get_details(self):
        return str(self.object)

    def get_confirm_url(self):
        return self.request.path

    def get_cancel_url(self):
        return self.success_url

    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)
