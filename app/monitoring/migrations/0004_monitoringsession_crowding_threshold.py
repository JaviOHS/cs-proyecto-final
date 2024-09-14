# Generated by Django 5.1 on 2024-09-14 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('monitoring', '0003_remove_monitoringsession_end_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='monitoringsession',
            name='crowding_threshold',
            field=models.IntegerField(default=10, help_text='Número de personas a partir del cual se considera aglomeración', verbose_name='Umbral de Aglomeración'),
        ),
    ]
