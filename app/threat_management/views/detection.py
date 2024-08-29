from django.views.generic import ListView
from app.threat_management.models import Detection

class DetectionListView(ListView):
    model = Detection
    template_name = 'threat_management/detection_list.html'
    context_object_name = 'detection_models'
    
    def get_queryset(self):
        return Detection.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Gestión de Amenazas"
        context["title2"] = "Modelos de Detección"
        return context