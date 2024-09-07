from django.views.generic import TemplateView
from app.monitoring.models import MonitoringSession

class HomeTemplateView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Inicio"
        if self.request.user.is_authenticated:
            monitoring_sessions = self.get_monitoring_sessions()
            if monitoring_sessions.exists():
                context['monitoring_sessions'] = monitoring_sessions
                context['session_id'] = monitoring_sessions.first().id
            else:
                context['monitoring_sessions'] = []
        else:
            context['monitoring_sessions'] = []
        return context
    
    def get_monitoring_sessions(self):
        return MonitoringSession.objects.filter(user=self.request.user)