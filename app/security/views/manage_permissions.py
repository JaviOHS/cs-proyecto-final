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

User = get_user_model()

class ManagePermissionsView(UserPermissionMixin, TemplateView):
    template_name = 'manage_permissions.html'
    permission_required = 'change_user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title1'] = 'Gestión de Permisos'
        users = User.objects.all()
        groups = Group.objects.all()
        permissions = Permission.objects.all()

        context.update({
            'users': users,
            'groups': groups, 
            'permissions': permissions
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
        context['title1'] = 'Actualizar Usuario'
        context['title2'] = 'Actualizar Información de Usuario'
        context['description'] = 'Complete el formulario con los datos del usuario.'
        return context
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def add_success_message(self):
        messages.success(self.request, "Éxito al actualizar usuario.")
    
class GroupCreateView(FormErrorHandlingMixin, UserPermissionMixin, CreateView):
    model = Group
    template_name = 'group_form.html'
    form_class = GroupForm
    success_url = reverse_lazy('security:manage_permissions')
    permission_required = 'add_group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title1'] = 'Crear Grupo'
        context['title2'] = 'Crear Grupo de Usuarios'
        context['description'] = 'Complete el formulario con los datos del grupo.'
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
        context['title1'] = 'Actualizar Grupo'
        context['title2'] = 'Actualizar Información de Grupo'
        context['description'] = 'Complete el formulario con los datos del grupo.'
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