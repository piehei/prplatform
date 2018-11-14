from django.db import models
from django.db.models import Count
from django.core.exceptions import EmptyResultSet
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

    def answers_in_ordered_list(self):
        return sorted(self.answers.all(), key=lambda a: self.exercise.question_order.index(a.question.pk))

    def __str__(self):
        return f"{self.submitter} -> {self.reviewed_submission.submitter} | {self.exercise}"

    def get_absolute_url(self):
        return reverse('courses:submissions:review-detail', kwargs={
            'base_url_slug': self.course.base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.exercise.pk,
            'sub_pk': self.pk
            })


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


class ReviewLockManager(models.Manager):

    def create_rlock(self, exercise, user, group=None):
        print(f"create_lock called for {exercise} {user} {group}")

        if exercise.use_groups and not group:
            raise Exception("Group info doesn't match")

        if not exercise.use_groups and group:
            raise Exception("Group info doesn't match")

        if exercise.type == ReviewExercise.RANDOM:
            print("type is RANDOM")

            """
                TODO: pick original submission based on some other heuristics
                      than just random value. something that has not received any
                      reviews?
            """

            # this is all _last_ submissions by other submitters sorted by review count
            osub_candidates = OriginalSubmission.objects \
                                           .filter(exercise=exercise.reviewable_exercise) \
                                           .annotate(Count('reviewlocks')) \
                                           .order_by('reviewlocks__count', 'created')

            # osub_candidates are now ordered so that first item has least reviewlocks
            # was created the longest time ago



            # ATTENTION !!!!!!!!!!
            # the query just above *CANNOT* be joined with the order_by/distinct queries
            # that's why we need two queries

            print(f"{osub_candidates.count()} -- before max_rev_per_sub exlude")
            osub_candidates = osub_candidates.exclude(reviewlocks__count__gte=exercise.max_reviews_per_submission)
            print(f"{osub_candidates.count()} -- after max_rev_per_sub exlude")

            if exercise.reviewable_exercise.use_groups:
                latest_submission_ids = OriginalSubmission.objects.filter(exercise=exercise.reviewable_exercise) \
                                                          .values('id') \
                                                          .order_by('submitter_group_id', '-created') \
                                                          .distinct('submitter_group_id')
                osub_candidates = osub_candidates.exclude(
                                                    submitter_group=exercise.course.find_studentgroup_by_user(user)) \
                                                 .filter(id__in=latest_submission_ids)

            else:
                latest_submission_ids = OriginalSubmission.objects.filter(exercise=exercise.reviewable_exercise) \
                                                          .values('id') \
                                                          .order_by('submitter_user_id', '-created') \
                                                          .distinct('submitter_user_id')
                osub_candidates = osub_candidates.exclude(submitter_user=user) \
                                                 .filter(id__in=latest_submission_ids)

            previous_revsub_ids = exercise.last_reviews_by(user).values('reviewed_submission__id')
            print(f"previous_revsub_ids: {previous_revsub_ids}")
            print(f"{osub_candidates.count()} -- before prev id exlude")
            osub_candidates = osub_candidates.exclude(pk__in=previous_revsub_ids)
            print(f"{osub_candidates.count()} -- after prev id exlude")
            osub_candidates = osub_candidates.filter(state=OriginalSubmission.READY_FOR_REVIEW)
            print(f"{osub_candidates.count()} -- after READY_FOR_REVIEW filter")

            if osub_candidates.count() == 0:
                raise EmptyResultSet("nothing to review")

            reviewable = osub_candidates.first()

        return self.create(user=user,
                           group=group,
                           review_exercise=exercise,
                           original_submission=reviewable)


class ReviewLock(TimeStampedModel):

    objects = ReviewLockManager()

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(StudentGroup, null=True, default=None, on_delete=models.CASCADE)
    original_submission = models.ForeignKey(OriginalSubmission, related_name="reviewlocks", on_delete=models.CASCADE)
    review_exercise = models.ForeignKey(ReviewExercise, on_delete=models.CASCADE)
    review_submission = models.ForeignKey(ReviewSubmission, null=True, default=None, on_delete=models.CASCADE)

    @property
    def owner(self):
        if self.group:
            return f"{self.group}"
        return f"self.user"
