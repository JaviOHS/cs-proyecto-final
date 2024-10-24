from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.db import IntegrityError

class AuthErrorHandlingMixin:
    redirect_authenticated_user = False
    
    def dispatch(self, request, *args, **kwargs):
        if self.redirect_authenticated_user and request.user.is_authenticated:
            redirect_to = self.get_authenticated_redirect_url()
            messages.info(request, "Ya has iniciado sesión.")
            return redirect(redirect_to)
        
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as ex:
            return self.handle_exception(ex)

    def get_authenticated_redirect_url(self):
        return reverse('home')

    def handle_exception(self, ex):
        error_message = str(ex)
        messages.error(self.request, f'Se ha producido un error inesperado: {error_message}')
        return redirect(f"{reverse('core:error_page')}?error_message={error_message}")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            self.add_success_message()
            return response
        except IntegrityError:
            messages.error(self.request, 'Ya existe una entrada con esta combinación de datos. Por favor, verifica e intenta de nuevo.')
            return self.form_invalid(form)
        except Exception as ex:
            return self.handle_exception(ex)

    def form_invalid(self, form):
        messages.error(self.request, 'Por favor, revise los campos del formulario.')
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{form[field].label if field in form.fields else ''} - {error}")
        return super().form_invalid(form)

    def add_success_message(self):
        if not messages.get_messages(self.request):
            messages.success(self.request, "Operación realizada con éxito.")