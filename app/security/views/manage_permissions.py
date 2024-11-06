from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.views.generic import UpdateView
from django.urls import reverse_lazy
from django.shortcuts import get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from app.security.mixins.permission_mixin import UserPermissionMixin
from django.views.generic import TemplateView, View
from app.security.forms.user_group_form import UserGroupForm
from app.security.forms.group_update_form import GroupUpdateForm

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

class UserUpdateView(UserPermissionMixin, UpdateView):
    model = User
    template_name = 'user_form.html'
    form_class = UserGroupForm
    success_url = reverse_lazy('security:manage_permissions')
    permission_required = 'change_user'

    def form_valid(self, form):
        messages.success(self.request, 'Usuario actualizado correctamente')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title1'] = 'Actualizar Usuario'
        context['title2'] = 'Actualizar Información de Usuario'
        context['description'] = 'Complete el formulario con los datos del usuario.'
        return context

class GroupUpdateView(UserPermissionMixin, UpdateView):
    model = Group
    template_name = 'group_update_form.html'
    form_class = GroupUpdateForm
    success_url = reverse_lazy('security:manage_permissions')
    permission_required = 'change_group'

    def form_valid(self, form):
        messages.success(self.request, 'Grupo actualizado correctamente')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title1'] = 'Actualizar Grupo'
        context['title2'] = 'Actualizar Información de Grupo'
        context['description'] = 'Complete el formulario con los datos del grupo.'
        return context

    