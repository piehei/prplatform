from django.urls import reverse
from django.db import models

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User
from prplatform.courses.models import Course

class BaseExercise(TimeStampedModel):
    name = models.CharField("Name of the exercise", max_length=100)
    course = models.ForeignKey(Course, 'exercises')

class FileUploadExercise(BaseExercise):
    file = models.FileField(upload_to='uploads/', blank=True)
