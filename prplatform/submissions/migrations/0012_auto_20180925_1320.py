# Generated by Django 2.0.6 on 2018-09-25 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0011_auto_20180923_1449'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='value_choice',
            field=models.CharField(blank=True, max_length=1, null=True),
        ),
        migrations.AlterField(
            model_name='answer',
            name='value_text',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]