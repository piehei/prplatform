# Generated by Django 2.1.4 on 2019-01-20 13:50

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('exercises', '0047_auto_20181126_1218'),
    ]

    operations = [
        migrations.CreateModel(
            name='AplusAPICallRequest',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('aplus_submission_data', django.contrib.postgres.fields.jsonb.JSONField()),
                ('submission_exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='exercises.SubmissionExercise')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]