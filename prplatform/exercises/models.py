from django.urls import reverse
from django.db import models

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User

class BaseExercise(TimeStampedModel):
    name = models.CharField("Name of the exercise", max_length=100)

