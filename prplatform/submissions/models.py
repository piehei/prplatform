from django.urls import reverse
from django.db import models

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User
from prplatform.courses.models import Course


class BaseSubmission(TimeStampedModel):

    course = models.ForeignKey(Course, related_name="submissions", on_delete=models.CASCADE)
    # TODO: Group submission?
    submitter = models.ForeignKey(User, related_name="submissions", on_delete=models.CASCADE)

    class Meta:
        abstract = True


class OriginalSubmission(BaseSubmission):
    """
        This describes a submission that is done to return something
        original to the service. This is not peer-reviewing.
        This is something that some other person will be peer-reviewing.
    """

    text = models.TextField(max_length=5000, blank=True)
    file = models.FileField(upload_to="uploads/", blank=True)
