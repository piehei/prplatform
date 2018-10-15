# Generated by Django 2.0.6 on 2018-10-15 07:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0016_course_aplus_apikey'),
        ('users', '0007_auto_20181013_0917'),
    ]

    operations = [
        migrations.AlterField(
            model_name='studentgroup',
            name='name',
            field=models.CharField(max_length=30),
        ),
        migrations.AlterUniqueTogether(
            name='studentgroup',
            unique_together={('course', 'name')},
        ),
    ]
