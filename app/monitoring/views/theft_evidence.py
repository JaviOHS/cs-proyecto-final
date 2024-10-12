from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from app.monitoring.models import MonitoringSession
from django.utils.translation import gettext_lazy as _  # Para traducir las variables dinámicas

class TheftEvidenceList(LoginRequiredMixin, DetailView):
    model = MonitoringSession
    template_name = 'theft_evidence.html'
    context_object_name = 'session' 

    def get_queryset(self):
        return MonitoringSession.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Monitoreo")
        context["title2"] = _("Evidencia de Robo")
        context["video_evidences"] = self.object.video_evidences.all() 
        return context
