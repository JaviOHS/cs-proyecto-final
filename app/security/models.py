from django.db import models
from django.contrib.auth.models import AbstractUser
from app.security.utils import validate_dni, phone_regex

class User(AbstractUser):
    dni = models.CharField(verbose_name='DNI', max_length=13, unique=True, validators=[validate_dni])
    image = models.ImageField(
        verbose_name='Archivo de Imagen', 
        default='componentes/default_user.jpg',
        upload_to='users/',
        max_length=1024,
        blank=True,
        null=True
    )
    phone = models.CharField(verbose_name='Celular', max_length=50, blank=True, null=True, validators=[phone_regex])
    email = models.EmailField(verbose_name='Correo Electrónico', max_length=254, unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f'{self.username}'
    
    def get_image(self):
        if self.image:
            return self.image.url
        return 'componentes/default_user.jpg'
    
    def save(self, *args, **kwargs):
        if self.pk:
            old_user = User.objects.get(pk=self.pk)
            if old_user.image and old_user.image != self.image:
                if old_user.image.name != 'componentes/usuario_anonimo.png':
                    old_user.image.delete(save=False)
        super().save(*args, **kwargs)
