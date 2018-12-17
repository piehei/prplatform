from django.db import OperationalError
from django.test import TestCase

from prplatform.exercises.models import (
        SubmissionExercise,
        ReviewExercise,
    )
from prplatform.submissions.models import (
        OriginalSubmission,
        ReviewSubmission,
    )
from prplatform.submissions.reviewlock_models import ReviewLock
from prplatform.users.models import User


class ReviewExerciseTestCase(TestCase):

    fixtures = [
        'courses.yaml'
    ]

    def setUp(self):
        self.se = SubmissionExercise.objects.get(name='T1 TEXT')
        self.course = self.se.course
        self.re = ReviewExercise.objects.get(name='T1 TEXT REVIEW')
        self.s1 = User.objects.get(username='student1')
        self.s2 = User.objects.get(username='student2')
        self.s3 = User.objects.get(username='student3')

    def test_save_and_destroy_lock_reviewsubmission(self):

        os = OriginalSubmission(course=self.course,
                                exercise=self.se,
                                submitter_user=self.s1,
                                text="jadajada")
        os.save()

        rl = ReviewLock(review_exercise=self.re,
                        user=self.s2,
                        original_submission=os)
        rl.save()

        rs = ReviewSubmission(course=self.course,
                              exercise=self.re,
                              submitter_user=self.s2,
                              reviewed_submission=os)

        self.assertEqual(ReviewLock.objects.count(), 1)
        rs.save_and_destroy_lock()
        self.assertEqual(ReviewLock.objects.count(), 0)

        rs2 = ReviewSubmission(course=self.course,
                               exercise=self.re,
                               submitter_user=self.s2,
                               reviewed_submission=os)
        self.assertRaises(OperationalError,
                          rs2.save_and_destroy_lock)

        rs2 = ReviewSubmission(course=self.course,
                               exercise=self.re,
                               submitter_user=self.s3,
                               reviewed_submission=os)
        self.assertRaises(OperationalError,
                          rs2.save_and_destroy_lock)
