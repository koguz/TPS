# Generated by Django 3.2.7 on 2021-10-28 09:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0004_mastertask_completed'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='developer',
            name='team',
        ),
        migrations.AddField(
            model_name='developer',
            name='team',
            field=models.ManyToManyField(blank=True, to='tasks.Team'),
        ),
    ]
