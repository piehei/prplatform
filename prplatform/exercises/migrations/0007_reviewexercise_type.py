# Generated by Django 2.0.4 on 2018-05-22 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0006_auto_20180518_1258'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewexercise',
            name='type',
            field=models.CharField(choices=[('RANDOM', 'Random by other user')], default='RANDOM', max_length=10),
        ),
    ]
