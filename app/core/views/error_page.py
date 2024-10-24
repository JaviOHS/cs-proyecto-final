from django.views.generic import TemplateView
from django.shortcuts import render

class ErrorPageTemplate(TemplateView):
    template_name = 'error_page.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title1"] = "Error"
        context["title2"] = "¡Lo sentimos! Ha ocurrido un error."  
        context["error_message"] = self.request.GET.get("error_message", "Ocurrió un error inesperado.")
        context["error_details"] = self.request.GET.get("error_details", "")
        context["image_url"] = self.request.GET.get("image_url", "img/error/default_error.png")
        return context
    
def custom_404_view(request, exception):
    context = {
        "title1": "Error 404",
        "title2": "Página no encontrada",
        "error_message": "La página que estás buscando no existe.",
        "error_details": "Es posible que la URL esté mal escrita o que la página haya sido eliminada.",
        "image_url": "img/error/404_image.png"
    }
    return render(request, 'error_page.html', context, status=404)

def custom_500_view(request):
    context = {
        "title1": "Error 500",
        "title2": "Error interno del servidor",
        "error_message": "Algo salió mal en el servidor.",
        "error_details": "Inténtalo de nuevo más tarde.",
        "image_url": "img/error/500_image.png"
    }
    return render(request, 'error_page.html', context, status=500)
