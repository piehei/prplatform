# Generated by Django 2.0.6 on 2018-09-13 12:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0005_auto_20180913_0650'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentgroup',
            name='name',
            field=models.CharField(max_length=30, unique=True),
        ),
    ]
