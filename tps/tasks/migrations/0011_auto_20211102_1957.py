# Generated by Django 3.2.7 on 2021-11-02 19:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0010_vote'),
    ]

    operations = [
        migrations.AddField(
            model_name='vote',
            name='status',
            field=models.SmallIntegerField(default=1, verbose_name='Status'),
        ),
        migrations.AlterField(
            model_name='comment',
            name='file_url',
            field=models.URLField(blank=True, max_length=512, null=True, verbose_name='URL'),
        ),
    ]
