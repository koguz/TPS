# Generated by Django 3.2.7 on 2021-11-26 19:07

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0018_milestonegrade'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='MilestoneGrade',
            new_name='TeamMilestoneGrade',
        ),
    ]
