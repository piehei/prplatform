# Generated by Django 2.1.2 on 2018-11-11 17:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0030_auto_20181101_1326'),
    ]

    operations = [
        migrations.AddField(
            model_name='reviewexercise',
            name='minimum_reviews_per_student',
            field=models.IntegerField(default=1, verbose_name='How many peer-reviews one student *HAS TO* complete before seeing peer-reviews by others'),
        ),
    ]