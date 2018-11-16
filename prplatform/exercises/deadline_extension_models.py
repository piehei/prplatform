from django.db import models

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User, StudentGroup
from prplatform.courses.models import Course
from .models import SubmissionExercise


class DeadlineExtension(TimeStampedModel):

    course = models.ForeignKey(Course, related_name='%(class)s_deadline_extensions',
                               on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='%(class)s_deadline_extensions', null=True,
                             on_delete=models.CASCADE)
    group = models.ForeignKey(StudentGroup, related_name='%(class)s_deadline_extensions',
                              null=True, on_delete=models.CASCADE)
    new_deadline = models.DateTimeField()

    class Meta:
        abstract = True


class SubmissionExerciseDeadlineExtension(DeadlineExtension):

    exercise = models.ForeignKey(SubmissionExercise, related_name='deadline_extensions',
                                 on_delete=models.CASCADE)
