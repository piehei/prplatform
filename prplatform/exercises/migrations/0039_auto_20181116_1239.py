# Generated by Django 2.1.2 on 2018-11-16 12:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0038_auto_20181116_1234'),
    ]

    operations = [
        migrations.AlterField(
            model_name='submissionexercisedeviation',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='submissionexercisedeviation_deviations', to='users.StudentGroup'),
        ),
        migrations.AlterField(
            model_name='submissionexercisedeviation',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='submissionexercisedeviation_deviations', to=settings.AUTH_USER_MODEL),
        ),
    ]
