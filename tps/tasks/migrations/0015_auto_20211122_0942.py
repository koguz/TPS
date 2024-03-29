# Generated by Django 3.2.9 on 2021-11-22 06:42

from django.db import migrations, models
import django.db.models.deletion
import tasks.models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0014_alter_like_owner'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mastertask',
            name='difficulty',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Easy'), (2, 'Normal'), (3, 'Difficult')], default=2, verbose_name='Difficulty'),
        ),
        migrations.AlterField(
            model_name='task',
            name='priority',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Low'), (2, 'Planned'), (3, 'Urgent')], default=2, verbose_name='Priority'),
        ),
        migrations.AlterField(
            model_name='task',
            name='promised_date',
            field=models.DateField(validators=[tasks.models.past_date_validator], verbose_name='Promised Date'),
        ),
        migrations.CreateModel(
            name='MasterTaskLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('taskstatus', models.CharField(max_length=64, verbose_name='Task Status')),
                ('tarih', models.DateTimeField()),
                ('log', models.TextField(verbose_name='Log')),
                ('mastertask', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='tasks.mastertask')),
            ],
        ),
    ]
