# Generated by Django 2.1.2 on 2018-11-09 08:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0016_course_aplus_apikey'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='hidden',
            field=models.BooleanField(default=True, verbose_name='Hide course from students'),
        ),
    ]
