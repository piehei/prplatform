# Generated by Django 2.1.2 on 2018-11-13 13:12

from django.db import migrations, models
import prplatform.submissions.models


class Migration(migrations.Migration):

    dependencies = [
        ('submissions', '0015_auto_20181109_1251'),
    ]

    operations = [
        migrations.AddField(
            model_name='answer',
            name='uploaded_file',
            field=models.FileField(blank=True, upload_to=prplatform.submissions.models.answer_upload_fp),
        ),
    ]
