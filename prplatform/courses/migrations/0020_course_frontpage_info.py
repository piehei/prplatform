# Generated by Django 2.1.7 on 2019-03-13 16:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0019_auto_20190121_1924'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='frontpage_info',
            field=models.TextField(blank=True, help_text='HTML works here. You can add titles, breaks, text-formatting etc.', null=True, verbose_name='Course info, news, notifications etc. to show on frontpage'),
        ),
    ]
