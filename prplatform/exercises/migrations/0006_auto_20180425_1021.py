# Generated by Django 2.0.4 on 2018-04-25 10:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0005_auto_20180425_1020'),
    ]

    operations = [
        migrations.AlterField(
            model_name='generalexercise',
            name='file_upload',
            field=models.BooleanField(default=False),
        ),
    ]
