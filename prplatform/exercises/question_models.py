from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.urls import reverse

from prplatform.courses.models import Course
from .models import ReviewExercise


class Choice(models.Model):
    course = models.ForeignKey(Course, related_name="question_choices", on_delete=models.CASCADE)
    text = models.CharField(max_length=50)

    def __str__(self):
        return self.text


class Question(models.Model):
    course = models.ForeignKey(Course, related_name="questions", on_delete=models.CASCADE)
    required = models.BooleanField(default=True)
    text = models.CharField(max_length=200)
    hide_from_receiver = models.BooleanField(default=False)
    choices = ArrayField(
                        ArrayField(models.CharField(max_length=20),
                                   size=2),
                        blank=True, null=True)

    def __str__(self):
        return f"Q: {self.text}"

    def get_absolute_url(self):
        return reverse('courses:exercises:question-detail', kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    def get_edit_url(self, exercise):
        return reverse('courses:exercises:question-update', kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'rpk': exercise.pk,
            'pk': self.pk
            })


class QuestionInUse(models.Model):
    exercise = models.ForeignKey(ReviewExercise, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.IntegerField()

    class Meta:
        ordering = ['value']


class ChoiceInUse(models.Model):
    choice = models.ForeignKey(Choice, on_delete=models.CASCADE)
    question_in_use = models.ForeignKey(Question, on_delete=models.CASCADE)
    value = models.IntegerField()
