from django.urls import reverse
from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField

from prplatform.core.models import TimeStampedModel
from prplatform.courses.models import Course
# from .question_models import Question


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

    def my_submissions(self, user):
        return self.submissions.filter(submitter=user)

    def submissions_by_submitter(self, user):
        if self.use_groups:
            return self.submissions.filter(submitter_group=self.course.find_studentgroup_by_user(user))
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
    SUBMISSION_EXERCISE_TYPE_CHOICES = (
            (TEXT, 'Student submits a text form'),
            (FILE_UPLOAD, 'Student uploads a file'),
            (APLUS, 'Submission is done in A+')
        )

    type = models.CharField(
            max_length=20,
            choices=SUBMISSION_EXERCISE_TYPE_CHOICES,
            default=FILE_UPLOAD
            )

    upload_instructions = models.CharField(max_length=500, blank=True)
    accepted_file_types = models.CharField(max_length=100, blank=True)

    use_states = models.BooleanField(default=False)

    aplus_course_id = models.IntegerField(null=True, blank=True)
    aplus_exercise_id = models.IntegerField(null=True, blank=True)

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
        return f"Submission exercise: {self.name}"

    def can_submit(self, user):
        if self.is_teacher(user):
            return True
        latest_submission = self.submissions_by_submitter(user).first()
        if latest_submission and latest_submission.state == latest_submission.BOOMERANG:
            return True
        if self.use_groups and \
           self.submissions.filter(submitter_group=self.course.find_studentgroup_by_user(user)):
            return False
        if self.submissions.filter(submitter_user=user):
            return False
        if not self.is_open():
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
    CHOOCE = 'CHOOCE'
    REVIEW_EXERCISE_TYPE_CHOICES = (
            (RANDOM, 'Random by other user'),
            (CHOOCE, 'Student chooces'),
        )

    type = models.CharField(
            max_length=10,
            choices=REVIEW_EXERCISE_TYPE_CHOICES,
            default=RANDOM
            )

    max_reviews_per_student = models.IntegerField("How many peer-reviews one student can do", default=1)
    max_reviews_per_submission = models.IntegerField("How many peer-reviews one submission can receive", default=1)
    model_answer = models.CharField("Model answer that the student may view in addition to peer-reviewable",
                                    blank=True,
                                    max_length=6000)
    questions = models.ManyToManyField('exercises.Question', related_name='exercises')
    question_order = ArrayField(models.IntegerField("PKs of questions"))

    def question_list_in_order(self):
        # TODO: THIS WILL THROW IF Q NOT IN self.question_order
        return sorted(self.questions.all(), key=lambda i: self.question_order.index(i.pk))

    def get_absolute_url(self):
        base_course = self.course.base_course
        return reverse('courses:exercises:review-detail', kwargs={
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
        return f"Review exercise: {self.name}"


