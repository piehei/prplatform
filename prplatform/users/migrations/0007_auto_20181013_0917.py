# Generated by Django 2.0.6 on 2018-10-13 09:17

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_auto_20180913_1207'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentgroup',
            name='student_usernames',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=100), size=None),
        ),
    ]