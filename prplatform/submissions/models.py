from django.db import models, OperationalError
from django.urls import reverse

import os

from prplatform.core.models import TimeStampedModel
from prplatform.users.models import User, StudentGroup
from prplatform.courses.models import Course
from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from prplatform.exercises.question_models import Question


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
            return self.submitter_group
        else:
            return self.submitter_user

    def is_owner(self, user):
        if self.submitter_group:
            return self.submitter_group.has_student(user)
        return self.submitter_user == user

    def get_absolute_url(self):
        urls = {'OriginalSubmission': 'courses:submissions:original-detail',
                'ReviewSubmission': 'courses:submissions:review-detail'}
        base_course = self.course.base_course
        return reverse(urls[self.__class__.__name__], kwargs={
            'base_url_slug': base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.exercise.pk,
            'sub_pk': self.pk
            })

    def get_delete_url(self):
        urls = {'OriginalSubmission': 'courses:submissions:original-delete',
                'ReviewSubmission': 'courses:submissions:review-delete'}
        return reverse(urls[self.__class__.__name__], kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.exercise.pk,
            'sub_pk': self.pk
            })


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
        # return f"Submitter: {self.submitter} | {self.exercise} ({str(self.created)[:16]})"
        return f"Submitter: {self.submitter} | {self.exercise}"

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

    def answers_in_ordered_list(self):
        return sorted(self.answers.all(), key=lambda a: self.exercise.question_order.index(a.question.pk))

    def __str__(self):
        return f"{self.submitter} -> {self.reviewed_submission.submitter} | {self.exercise}"

    def save_and_destroy_lock(self, *args, **kwargs):

        if self.pk is not None:

            raise OperationalError('This cannot be used to update the instance!')

        else:

            locks = self.exercise.reviewlocks_for(self.submitter_user)
            if locks.count() != 1:
                raise OperationalError(f'There should be exactly 1 reviewlock! Found: {locks.count()}')
            locks.first().delete()
            super().save(*args, **kwargs)


def answer_upload_fp(instance, filename):
    """ This will be the filename of the uploaded file """
    return f"uploads/course_{instance.submission.course.pk}/" + \
           f"answers_{instance.submission.exercise.pk}/ans_{instance.submission.pk}/{filename}"


class Answer(models.Model):

    submission = models.ForeignKey(ReviewSubmission, related_name="answers", on_delete=models.CASCADE)
    question = models.ForeignKey(Question, related_name="answers", on_delete=models.CASCADE)
    value_text = models.CharField(max_length=5000, blank=True, null=True)
    value_choice = models.CharField(max_length=20, blank=True, null=True)
    uploaded_file = models.FileField(upload_to=answer_upload_fp, blank=True)

    def save(self, *args, **kwargs):
        """ Overrides the model's save method so that when a file is uploaded
            its name may contain the object's PK. The PK would not be available
            at the save time since the row wouldn't have been written to the DB
            just yet.
        """
        if self.pk is None:
            uploaded_file = self.uploaded_file
            self.uploaded_file = None
            super().save(*args, **kwargs)
            self.uploaded_file = uploaded_file

        super().save(*args, **kwargs)

    def get_download_url(self):
        return reverse('courses:submissions:download', kwargs={
            'base_url_slug': self.submission.course.base_course.url_slug,
            'url_slug': self.submission.course.url_slug,
            'pk': self.pk
            }) + "?type=answer"

