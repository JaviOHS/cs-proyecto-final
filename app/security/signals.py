from django.contrib.auth.models import Group, Permission
from django.db.models.signals import post_save, post_migrate
from django.dispatch import receiver
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from app.security.models import User
from django.apps import apps
from config.utils import YELLOW_COLOR, GREEN_COLOR, RESET_COLOR, BLUE_COLOR

@receiver(post_save, sender=User)
def assign_user_group(sender, instance, created, **kwargs):
    if created:
        group_name = 'Administradores' if instance.is_superuser else 'Clientes'
        group, _ = Group.objects.get_or_create(name=group_name)
        instance.groups.add(group)
        print(f"{GREEN_COLOR}Usuario '{instance.username}' asignado al grupo '{group_name}'{RESET_COLOR}")

@receiver(post_migrate)
def setup_groups_and_permissions(sender, **kwargs):
    app_config = apps.get_app_config('security')
    if sender.name == app_config.name:
        with transaction.atomic():
            ensure_content_types_exist()
            create_groups_and_assign_permissions()
            create_client_user()
            create_admin_user()

def create_groups_and_assign_permissions():
    permissions_by_group = {
        'Clientes': [
            ('view_alarm', 'alarm', 'Alarm'),
            ('add_alarm', 'alarm', 'Alarm'),
            ('change_alarm', 'alarm', 'Alarm'),
            ('delete_alarm', 'alarm', 'Alarm'),
            ('view_detection', 'threat_management', 'Detection'),
            ('view_monitoringsession', 'monitoring', 'MonitoringSession'),
            ('add_monitoringsession', 'monitoring', 'MonitoringSession'),
            ('change_monitoringsession', 'monitoring', 'MonitoringSession'),
            ('delete_monitoringsession', 'monitoring', 'MonitoringSession'),
            ('view_user', 'security', 'User'),
        ],
        'Administradores': None,  # Will be assigned all permissions
    }

    for group_name, permission_info in permissions_by_group.items():
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            print(f"{GREEN_COLOR}Grupo '{group_name}' creado.{RESET_COLOR}")

        if permission_info is None:
            group.permissions.set(Permission.objects.all())
            print(f"{GREEN_COLOR}Todos los permisos asignados al grupo '{group_name}'.{RESET_COLOR}")
        else:
            for codename, app_label, model in permission_info:
                content_type = ContentType.objects.get(app_label=app_label, model=model.lower())
                permission, created = Permission.objects.get_or_create(
                    codename=codename,
                    content_type=content_type,
                    defaults={'name': f'Can {codename.split("_")[0]} {model}'}
                )
                if created:
                    print(f"{BLUE_COLOR}Permiso '{codename}' creado.{RESET_COLOR}")
                group.permissions.add(permission)
            print(f"{GREEN_COLOR}Permisos asignados al grupo '{group_name}'.{RESET_COLOR}")

def create_client_user():
    email = "ramon@gmail.com"
    if not User.objects.filter(email=email).exists():
        User.objects.create_user(
            email=email,
            username="Ramoncitox_",
            first_name="Ramón",
            last_name="Común",
            dni="0912345678",
            phone="0987654321",
            password="secret_password"
        )
        print(f"{YELLOW_COLOR}Usuario cliente 'Ramoncitox_' creado.{RESET_COLOR}")
    else:
        print(f"{BLUE_COLOR}El usuario cliente 'Ramoncitox_' ya existe.{RESET_COLOR}")

def create_admin_user():
    email = "dot40772@gmail.com"
    if not User.objects.filter(email=email).exists():
        User.objects.create_superuser(
            email=email,
            username="Javicho",
            first_name="Javier",
            last_name="OHS",
            dni="0981234567",
            phone="0987654321",
            password="secret_password"
        )
        print(f"{YELLOW_COLOR}Superusuario 'Javicho' creado.{RESET_COLOR}")
    else:
        print(f"{BLUE_COLOR}El superusuario 'Javicho' ya existe.{RESET_COLOR}")

def ensure_content_types_exist():
    models_to_check = [
        ('alarm', 'Alarm'),
        ('threat_management', 'Detection'),
        ('monitoring', 'MonitoringSession'),
        ('security', 'User'),
    ]
    for app_label, model in models_to_check:
        content_type, created = ContentType.objects.get_or_create(
            app_label=app_label,
            model=model.lower()
        )
        if created:
            print(f"{GREEN_COLOR}ContentType creado para {app_label}.{model}{RESET_COLOR}")