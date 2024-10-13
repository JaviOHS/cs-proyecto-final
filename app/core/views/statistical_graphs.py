from django.views.generic import TemplateView
from django.db.models import Count
import plotly.graph_objects as go
import plotly.offline as pyo
from app.threat_management.models import DetectionCounter
from django.db.models import Sum
from app.core.views.confirm_delete import ConfirmDeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _ # Para traducir las variables dinámicas

class StatisticalGraphsTemplate(TemplateView):
    template_name = 'statistical_graphs.html'
    
    def get_queryset(self):
        return DetectionCounter.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = _("Estadísticas")
        context["title1"] = _("Estadísticas")
        context["title2"] = _("Gráficos Estadísticos")
        context["details"] = _("Visualización de datos estadísticos de detección de amenazas.")

        # ---> Gráfico de Barras de Detecciones
        detection_data = (
            DetectionCounter.objects
            .values('detection__name')
            .annotate(total_count=Sum('count'))
            .filter(user=self.request.user)  # Filtrar por usuario actual
            .order_by('detection__name')
        )

        if not detection_data:
            messages.warning(self.request, 'No hay datos de detección disponibles.')
            context['bar_chart'] = '' 
            return context

        detection_names = [item['detection__name'] for item in detection_data]
        counts = [item['total_count'] for item in detection_data]

        print("Datos de Detección:")
        for name, count in zip(detection_names, counts):
            print(f"Amenaza: {name}, Total de Detecciones: {count}")

        bar_chart = go.Figure(data=[go.Bar(
            x=detection_names,
            y=counts,
            marker=dict(color='blue')
        )])

        bar_chart.update_layout(
            title='Cantidad de Amenazas Detectadas',
            xaxis_title='Amenazas',
            yaxis_title='Número de Detecciones',
            template='plotly_white',
            plot_bgcolor='rgba(255, 255, 255, 0)',  # Fondo del gráfico transparente
            paper_bgcolor='rgba(255, 255, 255, 0)'   # Fondo del papel transparente
        )

        context['bar_chart'] = pyo.plot(bar_chart, auto_open=False, include_plotlyjs=False, output_type='div')

        return context
