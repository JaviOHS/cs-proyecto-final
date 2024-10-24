from django.views.generic import TemplateView
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .graphs_generator import GraphGenerator
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

User = get_user_model()
class Plantilla(TemplateView):
    template_name = 'statistics_format.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Información Estadísticas")
        today = datetime.now()
        expiry_date = today + timedelta(days=7)
        context['expiry_date'] = expiry_date.strftime("%d de %B, %Y")
        graph_generator = GraphGenerator(user=self.request.user)
        context['bar_chart'] = graph_generator.bar_chart_detections()
        context['pie_chart'] = graph_generator.pie_chart_detections()
        context['line_chart_detections_by_day'] = graph_generator.line_chart_detections_by_day()
        context['total_threats'] = graph_generator.get_total_threats()
        context['threat_types'] = graph_generator.get_threat_types()
        context['next_day_prediction'] = graph_generator.get_next_day_prediction()
        context['last_prediction_date'] = graph_generator.get_last_prediction_date()
        context['threat_details'] = graph_generator.get_threat_details()
        if not context['bar_chart']:
            messages.warning(self.request, _('No hay datos de detección disponibles.'))
        return context
    
