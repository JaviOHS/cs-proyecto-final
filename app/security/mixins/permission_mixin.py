from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy

class UserPermissionMixin(UserPassesTestMixin):
    permission_required = ''
    paginate_by = 8
    
    def test_func(self):
        """Verifica si el usuario tiene permisos para acceder a la vista."""
        if not hasattr(self, 'get_object'): # Si es una vista de lista, permitir acceso
            return True
        
        try:
            obj = self.get_object()                 # Intentar obtener el objeto
            return obj.user == self.request.user    # Verificar si el usuario es el creador del objeto
        except AttributeError:
            return True # Si no hay objeto para verificar, permitir acceso

    def handle_no_permission(self):
        """Maneja el caso en que el usuario no tiene permisos para acceder a la vista."""
        if self.request.user.is_authenticated:
            messages.error(self.request, 'No tiene permiso para acceder a esta página.')
        else:
            messages.warning(self.request, 'Por favor inicie sesión para acceder a esta página.')
        return redirect('home')

    def _get_permissions_to_validate(self):
        """Obtiene los permisos a validar, según la configuración de la vista."""
        if not self.permission_required:
            return ()
        if isinstance(self.permission_required, str):
            permissions = (self.permission_required,)
        else:
            permissions = tuple(self.permission_required)
        return permissions
    
    def _get_permission_dict_of_group(self):
        """Obtiene un diccionario con los permisos del grupo del usuario."""
        user = self.request.user
        group = user.get_group_session(self.request)

        if group:
            permissions = group.permissions.all()
            return {perm.codename: perm.name for perm in permissions}

        return {}

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        try:
            if not request.user.is_authenticated:
                messages.warning(request, 'Por favor inicie sesión para acceder a esta página.')
                return redirect('login')
        
            user = request.user
            user.set_group_session(request)  # Asegurarse de que el grupo esté en la sesión.

            if 'group_id' not in request.session:
                messages.info(request, 'No hay grupo en la sesión')
                return redirect('home')
            
            if user.is_superuser: # Si es superusuario, tiene acceso a todo.
                return super().dispatch(request, *args, **kwargs)

            group = user.get_group_session(request)
            if group is None:
                messages.error(request, 'No se pudo obtener el grupo del usuario')
                return redirect('home')

            permissions = self._get_permissions_to_validate()
            if not permissions: # Si no se especifican permisos, permitir acceso.
                messages.info(request, 'No se especificaron permisos para la vista. Permitiendo acceso.')
                return super().dispatch(request, *args, **kwargs)

            if not group.permissions.filter(codename__in=permissions).exists():
                messages.error(request, 'No tiene permiso para ingresar a este módulo')
                return redirect('home')

            # messages.info(request, 'Permisos validados correctamente. Permitiendo acceso.')
            return super().dispatch(request, *args, **kwargs)

        except Exception as ex:
            import traceback
            print(f"Excepción en dispatch: {ex}")
            print(f"Tipo de excepción: {type(ex).__name__}")
            print(f"Traceback: {traceback.format_exc()}")
            error_message = f'Error de permisos: {ex}'
            error_details = str(ex)
            return redirect(f"{reverse('core:error_page')}?error_message={error_message}&error_details={error_details}")

    def get_context_data(self, **kwargs):
        """Agrega los permisos del grupo al contexto de la vista."""
        context = super().get_context_data(**kwargs)
        context['permissions'] = self._get_permission_dict_of_group()
        return context
