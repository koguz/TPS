# Generated by Django 3.2.7 on 2021-11-04 05:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0013_like'),
    ]

    operations = [
        migrations.AlterField(
            model_name='like',
            name='owner',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.developer'),
        ),
    ]
