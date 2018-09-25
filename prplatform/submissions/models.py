from django.db import models
from django.db.models import Count
from django.core.exceptions import FieldError
from django.urls import reverse

import os

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User, StudentGroup
from prplatform.courses.models import Course
from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from prplatform.exercises.question_models import Question, Choice


class BaseSubmission(TimeStampedModel):

    course = models.ForeignKey(Course, related_name="%(class)s_submissions", on_delete=models.CASCADE)
    submitter_user = models.ForeignKey(User, related_name="%(class)s_submitters", on_delete=models.CASCADE)
    submitter_group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, null=True)

    class Meta:
        abstract = True
        ordering = ['-created']

    @property
    def submitter(self):
        if self.submitter_group:
            return self.submitter_group.name
        else:
            return self.submitter_user.username

    def is_owner(self, user):
        if self.submitter_group:
            return self.submitter_group.has_student(user)
        return self.submitter_user == user


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

    SUBMITTED = 'submitted'
    BOOMERANG = 'boomerang'
    READY_FOR_REVIEW = 'ready_for_review'

    SUBMISSION_STATE_CHOICES = (
        (SUBMITTED, 'Submitted'),
        (BOOMERANG, 'Boomerang'),
        (READY_FOR_REVIEW, 'Ready for review'),
    )
    state = models.CharField(
        max_length=16,
        choices=SUBMISSION_STATE_CHOICES,
        default=READY_FOR_REVIEW,
    )

    def __str__(self):
        return str(self.created) + ": " + str(self.submitter) + " " + str(self.exercise)

    def filecontents_or_none(self):
        if self.file and os.path.splitext(self.file.name)[1] in ['.py', '.txt']:
            try:
                return self.file.read().decode("utf-8")
            except Exception:
                pass
        return None

    def submissions_by_same_submitter(self):
        all_subs = OriginalSubmission.objects.filter(exercise=self.exercise)
        if self.exercise.use_groups:
            return all_subs.filter(submitter_group=self.submitter_group)
        else:
            return all_subs.filter(submitter_user=self.submitter_user)

    def get_absolute_url(self):
        return reverse('courses:submissions:original-detail', kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.exercise.pk,
            'sub_pk': self.pk
            })

    def get_file_download_url(self):
        return reverse('courses:submissions:download', kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    def get_update_state_url(self):
        return reverse('courses:update-submission-state', kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
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
            super().save(*args, **kwargs)
            self.file = uploaded_file

        super().save(*args, **kwargs)


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
    value_text = models.CharField(max_length=1000, blank=True)
    value_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, blank=True, null=True)


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

            # this is all _last_ submissions by other submitters sorted by review count
            candidates = OriginalSubmission.objects \
                                           .filter(exercise=exercise.reviewable_exercise) \
                                           .annotate(Count('reviews')) \
                                           .order_by('reviews__count')

            if exercise.reviewable_exercise.use_groups:
                latest_submission_ids = OriginalSubmission.objects.values('id') \
                                                          .order_by('submitter_group_id', '-created') \
                                                          .distinct('submitter_group_id')
                candidates = candidates.exclude(
                                        submitter_group=exercise.course.find_studentgroup_by_user(user)) \
                                       .filter(id__in=latest_submission_ids)
            else:
                latest_submission_ids = OriginalSubmission.objects.values('id') \
                                                          .order_by('submitter_user_id', '-created') \
                                                          .distinct('submitter_user_id')
                candidates = candidates.exclude(
                                        submitter_user=user) \
                                       .filter(id__in=latest_submission_ids)

            if candidates.count() == 0:
                raise FieldError("nothing to review")

            reviewable = candidates.first()

        return self.create(user=user,
                           review_exercise=exercise,
                           original_submission=reviewable)


class ReviewLock(TimeStampedModel):

    objects = ReviewLockManager()

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    original_submission = models.ForeignKey(OriginalSubmission, on_delete=models.CASCADE)
    review_exercise = models.ForeignKey(ReviewExercise, on_delete=models.CASCADE)
    review_submission = models.ForeignKey(ReviewSubmission, null=True, default=None, on_delete=models.CASCADE)

