from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    dni = models.CharField(verbose_name='DNI', max_length=13, unique=True, blank=True, null=True)
    image = models.ImageField(
        verbose_name='Archivo de Imagen',
        upload_to='users/',
        max_length=1024,
        blank=True,
        null=True
    )
    phone=models.CharField(verbose_name='Celular',max_length=50,blank=True,null=True)
    email=models.EmailField(verbose_name='Correo Electrónico',max_length=254,unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username", "first_name", "last_name"]

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return '{}'.format(self.username)

    @property
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_groups(self):
        return self.groups.all()

    def get_short_name(self):
        return self.username
    
    def get_image(self):
        if self.image:
            return self.image.url
        else:
            return '/static/img/usuario_anonimo.png'
