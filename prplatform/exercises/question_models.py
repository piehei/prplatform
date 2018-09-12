from django.db import models
from django.urls import reverse

from .models import Course, ReviewExercise


class QuestionChoice(models.Model):
    course = models.ForeignKey(Course, related_name="question_choices", on_delete=models.CASCADE)
    text = models.CharField(max_length=50)
    value = models.IntegerField()

    def __str__(self):
        return self.text


class Question(models.Model):
    course = models.ForeignKey(Course, related_name="questions", on_delete=models.CASCADE)
    exercise = models.ManyToManyField(ReviewExercise, related_name="questions")
    text = models.CharField(max_length=200)
    order = models.IntegerField(default=0)
    choices = models.ManyToManyField(QuestionChoice, blank=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Q: {self.text}"

    def get_absolute_url(self):

        return reverse('courses:exercises:question-detail', kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    def get_edit_url(self):
        return reverse('courses:update-question', kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })
