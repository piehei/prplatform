from django.db import models
from django.db.models import Count
from django.core.exceptions import FieldError
from django.urls import reverse

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

    def get_absolute_url(self):
        return reverse('courses:submissions:original-detail', kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.exercise.pk,
            'sub_pk': self.pk
            })

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

    def get_absolute_url(self):
        return reverse('courses:submissions:review-detail', kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.exercise.pk,
            'sub_pk': self.pk
            })


class Answer(models.Model):

    submission = models.ForeignKey(ReviewSubmission, related_name="answers", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE)
    value = models.CharField(max_length=1000)


class ReviewLockManager(models.Manager):

    def create_rlock(self, exercise, user):
        print(f"create_lock called for {exercise} {user}")

        if exercise.type == ReviewExercise.RANDOM:
            print("type is RANDOM")

            """
                TODO: pick original submission based on some other heuristics
                      than just random value. something that has not received any
                      reviews?
            """

            # this is a list of all original submissions available for peer-reviewing
            # sorted in ascending order (from zero to n)
            reviewable_list = OriginalSubmission.objects \
                                                .exclude(submitter=user) \
                                                .filter(exercise=exercise.reviewable_exercise) \
                                                .annotate(Count('reviews')) \
                                                .order_by('reviews__count')

            # this most likely has no reviews yet
            # -> should they also be ordered by submission time?
            if len(reviewable_list) == 0:
                raise FieldError("nothing to review")

            reviewable = reviewable_list[0]

        return self.create(user=user,
                           review_exercise=exercise,
                           original_submission=reviewable)


class ReviewLock(TimeStampedModel):

    objects = ReviewLockManager()

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_submission = models.ForeignKey(OriginalSubmission, on_delete=models.CASCADE)
    review_exercise = models.ForeignKey(ReviewExercise, on_delete=models.CASCADE)
    review_submission = models.ForeignKey(ReviewSubmission, null=True, default=None, on_delete=models.CASCADE)

