# Generated by Django 2.0.6 on 2018-10-22 05:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0013_auto_20180925_1335'),
    ]

    operations = [
        migrations.AlterField(
            model_name='answer',
            name='value_text',
            field=models.CharField(blank=True, max_length=5000, null=True),
        ),
    ]
