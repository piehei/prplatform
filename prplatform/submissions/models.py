from django.urls import reverse
from django.db import models

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User
from prplatform.courses.models import Course
from prplatform.exercises.models import SubmissionExercise, ReviewExercise, Question


class BaseSubmission(TimeStampedModel):

    course = models.ForeignKey(Course, related_name="%(class)s_submissions", on_delete=models.CASCADE)
    # TODO: Group submission?
    submitter = models.ForeignKey(User, related_name="%(class)s_submitters", on_delete=models.CASCADE)

    class Meta:
        abstract = True


def upload_fp(instance, filename):
    """ This will be the filename of the uploaded file """
    return f"uploads/course_{instance.course.pk}/ex_{instance.exercise.pk}/sub_{instance.pk}/{filename}"


class OriginalSubmission(BaseSubmission):
    """
        This describes a submission that is done to return something
        original to the service. This is not peer-reviewing.
        This is something that some other person will be peer-reviewing.
    """

    exercise = models.ForeignKey(SubmissionExercise, related_name="submissions", on_delete=models.CASCADE)
    text = models.TextField(max_length=5000, blank=True)
    file = models.FileField(upload_to=upload_fp, blank=True)

    def __str__(self):
        return str(self.created) + ": " + str(self.submitter) + " " + str(self.exercise)

    def save(self, *args, **kwargs):
        """ Overrides the model's save method so that when a file is uploaded
            its name may contain the object's PK. The PK would not be available
            at the save time since the row wouldn't have been written to the DB
            just yet.
        """
        if self.pk is None:
            uploaded_file = self.file
            self.file = None
            super(OriginalSubmission, self).save(*args, **kwargs)
            self.file = uploaded_file

        super(OriginalSubmission, self).save(*args, **kwargs)


class ReviewSubmission(BaseSubmission):

    exercise = models.ForeignKey(ReviewExercise, related_name="submissions", on_delete=models.CASCADE)
    reviewed_submission = models.ForeignKey(OriginalSubmission, related_name="reviews", on_delete=models.CASCADE)

    def __str__(self):
        return str(self.created) + ": " + str(self.submitter) + " " + str(self.exercise)


class Answer(models.Model):

    submission = models.ForeignKey(ReviewSubmission, related_name="answers", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE)
    value = models.CharField(max_length=1000)
