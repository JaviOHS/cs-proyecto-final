from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.views.generic import UpdateView, CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from app.security.mixins.permission_mixin import UserPermissionMixin
from app.security.mixins.form_error_handling import FormErrorHandlingMixin
from django.views.generic import TemplateView
from app.security.forms.user_group_form import UserGroupForm
from app.security.forms.group_form import GroupForm
from app.core.views.confirm_delete import ConfirmDeleteView
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class ManagePermissionsView(UserPermissionMixin, TemplateView):
    template_name = 'manage_permissions.html'
    permission_required = 'change_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title1'] = _("Gestión de Permisos")
        query = self.request.GET.get('query', '')

        if query:
            users = User.objects.filter(
                Q(username__icontains=query) |
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query)
            )
        else:
            users = User.objects.all()
        
        context.update({
            'users': users,
            'groups': Group.objects.all(),
            'permissions': Permission.objects.all(),
            'query': query
        })
        return context
    
class UserUpdateView(FormErrorHandlingMixin, UserPermissionMixin, UpdateView):
    model = User
    template_name = 'user_form.html'
    form_class = UserGroupForm
    success_url = reverse_lazy('security:manage_permissions')
    permission_required = 'change_user'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title1'] = _("Actualizar Usuario")
        context['title2'] = _("Actualizar Información de Usuario")
        context['description'] = _("Complete el formulario con los datos del usuario.")
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def add_success_message(self):
        messages.success(self.request, "Éxito al actualizar usuario.")
    
class UserDeleteView(FormErrorHandlingMixin, UserPermissionMixin, ConfirmDeleteView):
    model = User
    success_url = reverse_lazy('security:manage_permissions')
    permission_required = 'delete_user'

    def get_details(self):
        return f"Usuario: {self.object.username}"
    
    def add_success_message(self):
        messages.success(self.request, "Éxito al eliminar usuario.")

class GroupCreateView(FormErrorHandlingMixin, UserPermissionMixin, CreateView):
    model = Group
    template_name = 'group_form.html'
    form_class = GroupForm
    success_url = reverse_lazy('security:manage_permissions')
    permission_required = 'add_group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title1'] = _("Crear Grupo")
        context['title2'] = _("Crear Grupo de Usuarios")
        context['description'] = _("Complete el formulario con los datos del grupo.")
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def add_success_message(self):
        messages.success(self.request, "Éxito al crear grupo.")
        
class GroupUpdateView(UserPermissionMixin, UpdateView):
    model = Group
    template_name = 'group_form.html'
    form_class = GroupForm
    success_url = reverse_lazy('security:manage_permissions')
    permission_required = 'change_group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title1'] = _("Actualizar Grupo")
        context['title2'] = _("Actualizar Información de Grupo")
        context['description'] = _("Complete el formulario con los datos del grupo.")
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def add_success_message(self):
        messages.success(self.request, "Éxito al actualizar grupo.")

class GroupDeleteView(FormErrorHandlingMixin, UserPermissionMixin, ConfirmDeleteView):
    model = Group
    success_url = reverse_lazy('security:manage_permissions')
    permission_required = 'delete_group'

    def get_details(self):
        return f"Grupo: {self.object.name}"
    
    def add_success_message(self):
        messages.success(self.request, "Éxito al eliminar grupo.")