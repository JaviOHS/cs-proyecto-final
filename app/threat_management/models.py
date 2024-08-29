from django.db import models

class Detection(models.Model):
    name = models.CharField(max_length=100, verbose_name='Nombre de Amenaza')
    description = models.TextField(max_length=500, verbose_name='Descripción')
    icon = models.CharField(max_length=100, verbose_name='Ícono')
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name