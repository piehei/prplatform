# Generated by Django 2.0.6 on 2018-09-27 08:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exercises', '0022_reviewexercise_question_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='reviewexercise',
            name='questions',
            field=models.ManyToManyField(related_name='exercises', to='exercises.Question'),
        ),
    ]
