from django.db import models
from django.urls import reverse

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User, StudentGroup
from prplatform.courses.models import Course
from .models import SubmissionExercise, ReviewExercise


class Deviation(TimeStampedModel):

    user = models.ForeignKey(User, related_name='%(class)s_deviations',
                             null=True, blank=True,
                             on_delete=models.CASCADE)
    group = models.ForeignKey(StudentGroup, related_name='%(class)s_deviations',
                              null=True, blank=True,
                              on_delete=models.CASCADE)
    new_deadline = models.DateTimeField()
    extra_submissions = models.PositiveIntegerField(default=0)

    class Meta:
        abstract = True

    def __str__(self):
        if self.group:
            return f"{self.group} | {self.extra_submissions} | {self.new_deadline}"
        else:
            return f"{self.user} | {self.extra_submissions} | {self.new_deadline}"

    def get_delete_url(self):
        urls = {'SubmissionExerciseDeviation': 'courses:exercises:submission-deviation-delete',
                'ReviewExerciseDeviation':     'courses:exercises:review-deviation-delete'}
        return reverse(urls[self.__class__.__name__], kwargs={
            'base_url_slug': self.exercise.course.base_course.url_slug,
            'url_slug': self.exercise.course.url_slug,
            'exer_pk': self.exercise.pk,
            'pk': self.pk
            })


class SubmissionExerciseDeviation(Deviation):

    exercise = models.ForeignKey(SubmissionExercise, related_name='deviations',
                                 on_delete=models.CASCADE)


class ReviewExerciseDeviation(Deviation):

    exercise = models.ForeignKey(ReviewExercise, related_name='deviations',
                                 on_delete=models.CASCADE)
