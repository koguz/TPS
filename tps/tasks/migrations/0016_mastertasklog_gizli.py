# Generated by Django 3.2.9 on 2021-11-22 06:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0015_auto_20211122_0942'),
    ]

    operations = [
        migrations.AddField(
            model_name='mastertasklog',
            name='gizli',
            field=models.BooleanField(default=False, verbose_name='Gizli'),
        ),
    ]
