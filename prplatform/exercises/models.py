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
    course = models.ForeignKey(Course, related_name='%(class)s_exercises', on_delete=models.CASCADE)
    description = models.CharField(max_length=5000, blank=True)

    @property
    def base_course(self):
        return self.course.base_course

    class Meta:
        abstract = True


class SubmissionExercise(BaseExercise):
    """ This is an exercise where the student uploads something to the system.
        This uploaded file shall be the answer to this exercise.
        This is NOT peer-reviewing but the thing that will be peer-reviewed.

        ReviewExercise describes the peer-reviewing task itself.
    """

    file_upload = models.BooleanField(default=False)
    upload_instructions = models.CharField(max_length=500, blank=True)

    def get_absolute_url(self):
        base_course = self.course.base_course
        return reverse('courses:exercises:detail', kwargs={
            'base_url_slug': base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })


class ReviewExercise(BaseExercise):
    """ This is an exercise that describes the peer-reviewing to be done.
        This tells what sort of peer-review should happen etc.
        This is NOT an exercise where the student returns some original
        answer and other students peer-review it.

        SubmissionExercise describes the returning of an original answer.
    """

    reviewable_exercise = models.ForeignKey(SubmissionExercise, on_delete=models.CASCADE)

