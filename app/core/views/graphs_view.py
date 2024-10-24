from django.views.generic import TemplateView
from django.contrib import messages
from app.threat_management.models import DetectionCounter
from django.utils.translation import gettext_lazy as _
from app.core.views.graphs_generator import GraphGenerator

class StatisticalGraphsTemplate(TemplateView):
    template_name = 'statistical_graphs.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Estadísticas")
        context["title2"] = _("Gráficos Estadísticos")
        context["details"] = _("Visualización de datos estadísticos de detección de amenazas.")
        graph_generator = GraphGenerator(user=self.request.user)

        context['bar_chart'] = graph_generator.bar_chart_detections()
        context['pie_chart'] = graph_generator.pie_chart_detections()
        context['line_chart_detections_by_day'] = graph_generator.line_chart_detections_by_day()

        if not context['bar_chart']:
            messages.warning(self.request, 'No hay datos de detección disponibles.')

        return context
