from django.urls import reverse
from django.db import models

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User
from prplatform.courses.models import Course


class BaseExercise(TimeStampedModel):
    """ This base exercise includes common fields for all exercises.
        A single exercise is something where the student can:
          * return his/her answer (teacher wants all to upload a pdf for instance)
          * make a peer-review of someone else's answer

        For each of the actual use-cases an inherited exercise shall be used.
    """

    name = models.CharField("Name of the exercise", max_length=100)
    course = models.ForeignKey(Course, related_name='exercises', on_delete=models.CASCADE)
    description = models.CharField(max_length=5000, blank=True)


class GeneralExercise(BaseExercise):
    """ This is an exercise where the student uploads something to the system.
        This uploaded file shall be the answer to this exercise.
        This is not peer-reviewing but the thing that will be peer-reviewed.
    """

    file_upload = models.BooleanField(default=False)
    upload_instructions = models.CharField(max_length=500, blank=True)

