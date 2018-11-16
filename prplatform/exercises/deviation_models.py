from django.db import models

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User, StudentGroup
from prplatform.courses.models import Course
from .models import SubmissionExercise


class Deviation(TimeStampedModel):

    course = models.ForeignKey(Course, related_name='%(class)s_deviations',
                               on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='%(class)s_deviations',
                             null=True, blank=True,
                             on_delete=models.CASCADE)
    group = models.ForeignKey(StudentGroup, related_name='%(class)s_deviations',
                              null=True, blank=True,
                              on_delete=models.CASCADE)
    new_deadline = models.DateTimeField()

    class Meta:
        abstract = True


class SubmissionExerciseDeviation(Deviation):

    exercise = models.ForeignKey(SubmissionExercise, related_name='deviations',
                                 on_delete=models.CASCADE)
