from django.contrib import messages
from django.db import IntegrityError
from django.http import Http404
from django.shortcuts import redirect
from django.urls import reverse

class FormErrorHandlingMixin:
    def dispatch(self, request, *args, **kwargs):
        try:
            return super().dispatch(request, *args, **kwargs)
        except Http404:
            messages.error(request, 'La página solicitada no se encontró.')
            return redirect(f"{reverse('core:error_page')}?error_message=La página solicitada no se encontró.")
        except Exception as ex:
            error_message = str(ex)
            print(f"Error en FormErrorHandlingMixin: {error_message}")
            messages.error(request, 'Se ha producido un error inesperado.')
            return redirect(f"{reverse('core:error_page')}?error_message={error_message}")

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            self.add_success_message()
            return response
        except IntegrityError as ex:
            messages.error(self.request, 'Ya existe una entrada con esta combinación de datos. Por favor, verifica e intenta de nuevo.')
            return self.form_invalid(form)
        except Exception as ex:
            error_message = str(ex)
            messages.error(self.request, f'Se ha producido un error inesperado en el formulario: {error_message}')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Revise los campos del formulario.')
        for field, errors in form.errors.items():
            if field in form.fields:
                for error in errors:
                    messages.error(self.request, f"{form.fields[field].label} - {error}")
            else:
                for error in errors:
                    messages.error(self.request, f"{error}")
        return super().form_invalid(form)

    def add_success_message(self):
        if not messages.get_messages(self.request):
            messages.success(self.request, "Operación realizada con éxito.")