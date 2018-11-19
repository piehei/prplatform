from django.apps import apps
from django.urls import reverse
from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField

from prplatform.core.models import TimeStampedModel
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

    opening_time = models.DateTimeField()
    closing_time = models.DateTimeField()

    visible_to_students = models.BooleanField(default=True)
    use_groups = models.BooleanField(default=False)

    @property
    def base_course(self):
        return self.course.base_course

    def is_teacher(self, user):
        return self.base_course.is_teacher(user)

    def is_open(self):
        return self.opening_time < timezone.now() and self.closing_time > timezone.now()

    def opens_in_future(self):
        return self.opening_time > timezone.now()

    def can_access(self, user):
        if self.is_teacher(user):
            return True

        if not self.visible_to_students:
            return False

        # if visible, anyone can access
        return True

    def deviation_for(self, user):
        if self.use_groups:
            return self.deviations.filter(
                    group=self.course.find_studentgroup_by_user(user)
                    ).first()
        else:
            return self.deviations.filter(user=user).first()

    def deadline_extension_for(self, user):

        deviation = self.deviation_for(user)
        if not deviation or deviation.new_deadline <= self.closing_time:
            return None
        return deviation

    def max_submissions_for(self, user):
        deviation = self.deviation_for(user)
        if not deviation:
            return self.max_submission_count
        return self.max_submission_count + deviation.extra_submissions

    def my_submissions(self, user):
        return self.submissions.filter(submitter=user)

    def submissions_by_submitter(self, user):

        if user.is_anonymous or not self.course.is_enrolled(user):
            return self.submissions.none()

        if self.use_groups:
            group = self.course.find_studentgroup_by_user(user)
            return self.submissions.exclude(submitter_group=None) \
                                   .filter(submitter_group=group)
        return self.submissions.filter(submitter_user=user)

    def get_list_url(self):
        urls = {'SubmissionExercise': 'courses:submissions:original-list',
                'ReviewExercise': 'courses:submissions:review-list'}
        base_course = self.course.base_course
        return reverse(urls[self.__class__.__name__], kwargs={
            'base_url_slug': base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    def get_deviations_list_url(self):
        urls = {'SubmissionExercise': 'courses:exercises:submission-deviation-list',
                'ReviewExercise': 'courses:exercises:review-deviation-list'}
        base_course = self.course.base_course
        return reverse(urls[self.__class__.__name__], kwargs={
            'base_url_slug': base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    def get_deviations_create_url(self):
        urls = {'SubmissionExercise': 'courses:exercises:submission-deviation-create',
                'ReviewExercise': 'courses:exercises:review-deviation-create'}
        base_course = self.course.base_course
        return reverse(urls[self.__class__.__name__], kwargs={
            'base_url_slug': base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    class Meta:
        abstract = True
        ordering = ['-closing_time']


class SubmissionExercise(BaseExercise):
    """ This is an exercise where the student uploads something to the system.
        This uploaded file shall be the answer to this exercise.
        This is NOT peer-reviewing but the thing that will be peer-reviewed.

        ReviewExercise describes the peer-reviewing task itself.
    """

    TEXT = 'TEXT'
    FILE_UPLOAD = 'FILE_UPLOAD'
    APLUS = 'APLUS'
    GROUP_NO_SUBMISSION = 'GROUP_NO_SUBMISSION'
    SUBMISSION_EXERCISE_TYPE_CHOICES = (
            (TEXT, 'Student submits a text form'),
            (FILE_UPLOAD, 'Student uploads a file'),
            (APLUS, 'Submission is done in A+'),
            (GROUP_NO_SUBMISSION, "Use this for group peer-reviews (students "
                                  "peer-review each other but don't return any original submissions)")
        )

    type = models.CharField(
            max_length=20,
            choices=SUBMISSION_EXERCISE_TYPE_CHOICES,
            default=FILE_UPLOAD
            )

    max_submission_count = models.IntegerField(default=1)

    upload_instructions = models.CharField(max_length=500, blank=True)
    accepted_filetypes = models.CharField(max_length=100, blank=True)

    use_states = models.BooleanField(default=False)

    aplus_course_id = models.IntegerField(null=True, blank=True)
    aplus_exercise_id = models.IntegerField(null=True, blank=True)

    def last_submission_by_submitters(self):
        """
        ALERT!!!!! This returns last submissions by submitter which means:
        if a submitter has done multiple submissions reviewing multiple
        OriginalSubmissions, only the last review is returned
        -----> DO NOT MOVE THIS TO REVIEWEXERCISE, MAKE A NEW IMPLEMENTATION
        """
        if self.use_groups:
            last_ids = self.submissions \
                           .values('id') \
                           .order_by('submitter_group_id', '-created') \
                           .distinct('submitter_group_id')
        else:
            last_ids = self.submissions \
                           .values('id') \
                           .order_by('submitter_user_id', '-created') \
                           .distinct('submitter_user_id')
        return self.submissions.filter(id__in=last_ids)

    def get_absolute_url(self):
        base_course = self.course.base_course
        return reverse('courses:exercises:submission-detail', kwargs={
            'base_url_slug': base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    def get_edit_url(self):
        base_course = self.course.base_course
        return reverse('courses:update-submission-exercise', kwargs={
            'base_url_slug': base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    def __str__(self):
        return f"{self.name}"

    def can_submit(self, user):
        if self.is_teacher(user):
            return True

        if user.is_anonymous:
            return False

        if not self.course.is_enrolled(user):
            return False

        if not self.is_open() and not self.deadline_extension_for(user):
            return False

        if self.use_groups and not self.course.find_studentgroup_by_user(user):
            return False

        submissions = self.submissions_by_submitter(user)
        latest_sub = submissions.first()
        if self.use_states and latest_sub:
            if latest_sub.state == latest_sub.BOOMERANG:
                return True

        # WARNING: do NOT move this above the BOOMERANG check
        if submissions.count() >= self.max_submissions_for(user):
            return False

        return True


class ReviewExercise(BaseExercise):
    """ This is an exercise that describes the peer-reviewing to be done.
        This tells what sort of peer-review should happen etc.
        This is NOT an exercise where the student returns some original
        answer and other students peer-review it.

        SubmissionExercise describes the returning of an original answer.
    """

    reviewable_exercise = models.OneToOneField(SubmissionExercise,
                                               related_name="review_exercise",
                                               on_delete=models.CASCADE)

    show_reviews_after_date = models.DateTimeField("Show peer-reviews only after this date",
                                                   blank=True, null=True)

    RANDOM = 'RANDOM'
    CHOOSE = 'CHOOSE'
    GROUP = 'GROUP'
    REVIEW_EXERCISE_TYPE_CHOICES = (
            (RANDOM, 'Random by other user (prefer oldest with least peer-reviews)'),
            (CHOOSE, 'Student chooses'),
            (GROUP, 'Students peer-review other students in their own group'),
        )

    type = models.CharField(
            max_length=10,
            choices=REVIEW_EXERCISE_TYPE_CHOICES,
            default=RANDOM
            )

    require_original_submission = models.BooleanField(
            "Student cannot peer-review others if she has not made the original submission", default=True)

    can_review_own_submission = models.BooleanField("Students can peer-review their own submissions", default=False)

    max_submission_count = models.IntegerField("How many peer-reviews one student can do", default=1)
    max_reviews_per_submission = models.IntegerField("How many peer-reviews one submission can receive", default=1)
    min_submission_count = models.IntegerField(
            "How many peer-reviews one student *HAS TO* complete before seeing peer-reviews by others", default=1)

    model_answer = models.CharField("Model answer that the student may view in addition to peer-reviewable",
                                    blank=True,
                                    max_length=6000)
    questions = models.ManyToManyField('exercises.Question', related_name='exercises')
    question_order = ArrayField(models.IntegerField("PKs of questions"))

    def question_list_in_order(self):
        # TODO: THIS WILL THROW IF Q NOT IN self.question_order
        return sorted(self.questions.all(), key=lambda i: self.question_order.index(i.pk))

    def reviews_available_date_in_future(self):
        if self.show_reviews_after_date and self.show_reviews_after_date > timezone.now():
            return True
        return False

    def last_reviews_for(self, user):

        all_reviews = None
        if self.use_groups:
            all_reviews = self.submissions.filter(
                    reviewed_submission__submitter_group=self.course.find_studentgroup_by_user(user)) \
                                          .order_by('submitter_group_id', '-created') \
                                          .distinct('submitter_group_id')
        else:
            all_reviews = self.submissions.filter(reviewed_submission__submitter_user=user) \
                                          .order_by('submitter_user_id', '-created') \
                                          .distinct('submitter_user_id')
        return all_reviews

    def review_showing_requirements_ok(self, user):

        reviews_by_user = self.last_reviews_by(user)

        if reviews_by_user.count() < self.min_submission_count:
            return False

        return True

    def last_reviews_by(self, user):

        all_reviews = None
        if self.use_groups:
            all_reviews = self.submissions.filter(submitter_group=self.course.find_studentgroup_by_user(user)) \
                                          .order_by('reviewed_submission__submitter_group_id', '-created') \
                                          .distinct('reviewed_submission__submitter_group_id')
        else:
            all_reviews = self.submissions.filter(submitter_user=user) \
                                          .order_by('reviewed_submission__submitter_user_id', '-created') \
                                          .distinct('reviewed_submission__submitter_user_id')
        return all_reviews

    def can_submit(self, user):
        if self.is_teacher(user):
            return True, None

        if user.is_anonymous:
            return False, None

        if not self.course.is_enrolled(user):
            return False, None

        if self.use_groups and not self.course.find_studentgroup_by_user(user):
            return False, None

        if not self.is_open() and not self.deadline_extension_for(user):
            return False, "not_open"

        if self.submissions_by_submitter(user).count() >= self.max_submissions_for(user):
            return False, "reviews_done"

        if self.original_submissions_by(user).count() == 0 \
                and self.require_original_submission:
            return False, "own_submission_missing"

        return True, None

    def original_submissions_by(self, user):
        return self.reviewable_exercise \
                   .submissions_by_submitter(user) \
                   .filter(state=apps.get_model('submissions', 'OriginalSubmission').READY_FOR_REVIEW)

    def reviewlocks_for(self, user):
        if self.use_groups:
            g = self.course.find_studentgroup_by_user(user)
            if not g:
                return self.reviewlock_set.none()
            return self.reviewlock_set.filter(group=g,
                                              review_exercise=self)
        return self.reviewlock_set.filter(user=user,
                                          review_exercise=self)

    def get_absolute_url(self):
        base_course = self.course.base_course
        return reverse('courses:exercises:review-detail', kwargs={
            'base_url_slug': base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    def get_question_url(self):
        base_course = self.course.base_course
        return reverse('courses:exercises:question-list', kwargs={
            'base_url_slug': base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    def get_edit_url(self):
        base_course = self.course.base_course
        return reverse('courses:update-review-exercise', kwargs={
            'base_url_slug': base_course.url_slug,
            'url_slug': self.course.url_slug,
            'pk': self.pk
            })

    def __str__(self):
        return f"{self.name}"

    def get_stats_url(self):
        base_course = self.course.base_course
        return reverse('courses:stats', kwargs={
                       'base_url_slug': base_course.url_slug,
                       'url_slug': self.course.url_slug,
                       'pk': self.pk
                       })

