from django.contrib.postgres.fields import JSONField
from django.db import models

from prplatform.core.models import TimeStampedModel
from prplatform.exercises.models import SubmissionExercise

class AplusAPICallRequest(TimeStampedModel):

    submission_exercise = models.ForeignKey(SubmissionExercise, on_delete=models.CASCADE)
    hook_data = JSONField()
