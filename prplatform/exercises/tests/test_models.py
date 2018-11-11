from django.test import TestCase
from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from prplatform.submissions.models import OriginalSubmission, ReviewSubmission
from prplatform.users.models import User

class ReviewExerciseTestCase(TestCase):

    fixtures = [
        'courses.yaml'
    ]

    def setUp(self):
        self.se = SubmissionExercise.objects.get(name='T1 TEXT')
        self.course = self.se.course
        self.re = ReviewExercise.objects.get(name='T1 TEXT REVIEW')
        self.student1 = User.objects.get(username='student1')
        self.student2 = User.objects.get(username='student2')
        self.student3 = User.objects.get(username='student3')

        self.sub1 = OriginalSubmission(course=self.course,
                                       exercise=self.se,
                                       text="jada jada",
                                       submitter_user=self.student1)
        self.sub1.save()
        self.sub2 = OriginalSubmission(course=self.course,
                                       exercise=self.se,
                                       text="jada jada",
                                       submitter_user=self.student2)
        self.sub2.save()

        for i in range(2):
            ReviewSubmission.objects.create(course=self.course,
                                            exercise=self.re,
                                            reviewed_submission=self.sub1,
                                            submitter_user=self.student2)
            ReviewSubmission.objects.create(course=self.course,
                                            exercise=self.re,
                                            reviewed_submission=self.sub1,
                                            submitter_user=self.student3)
            ReviewSubmission.objects.create(course=self.course,
                                            exercise=self.re,
                                            reviewed_submission=self.sub2,
                                            submitter_user=self.student3)

    def test_last_submission_by_submitters(self):

        last_subs = self.se.last_submission_by_submitters()
        self.assertEqual(last_subs.count(), 2)
        self.assertNotEqual(last_subs[0].submitter_user, last_subs[1].submitter_user)

        sub12 = OriginalSubmission(course=self.course,
                                   exercise=self.se,
                                   text="jada jada",
                                   submitter_user=self.student1)
        sub12.save()
        sub22 = OriginalSubmission(course=self.course,
                                   exercise=self.se,
                                   text="jada jada",
                                   submitter_user=self.student2)
        sub22.save()
        last_subs_again = self.se.last_submission_by_submitters()
        self.assertEqual(last_subs_again.count(), 2)
        self.assertNotEqual(last_subs.filter(submitter_user=self.student1),
                            last_subs_again.filter(submitter_user=self.student1))
        self.assertNotEqual(last_subs.filter(submitter_user=self.student2),
                            last_subs_again.filter(submitter_user=self.student2))
        self.assertEqual(sub12 in last_subs_again, True)
        self.assertEqual(sub22 in last_subs_again, True)

    def test_last_reviews_for(self):
        self.assertEqual(self.re.last_reviews_for(self.student1).count(), 2)
        self.assertEqual(self.re.last_reviews_for(self.student2).count(), 1)
        self.assertEqual(self.re.last_reviews_for(self.student3).count(), 0)

        last_for_before_change = self.re.last_reviews_for(self.student1).filter(submitter_user=self.student3).first()

        ReviewSubmission.objects.create(course=self.course,
                                        exercise=self.re,
                                        reviewed_submission=self.sub1,
                                        submitter_user=self.student3)

        last_for_after_change = self.re.last_reviews_for(self.student1).filter(submitter_user=self.student3).first()
        self.assertNotEqual(last_for_before_change, last_for_after_change)
        self.assertEqual(self.re.last_reviews_for(self.student1).count(), 2)

    def test_last_reviews_by(self):
        self.assertEqual(self.re.last_reviews_by(self.student1).count(), 0)
        self.assertEqual(self.re.last_reviews_by(self.student2).count(), 1)
        self.assertEqual(self.re.last_reviews_by(self.student3).count(), 2)

        last_by_before_change = self.re.last_reviews_by(self.student3) \
                                       .filter(reviewed_submission__submitter_user=self.student1).first()

        ReviewSubmission.objects.create(course=self.course,
                                        exercise=self.re,
                                        reviewed_submission=self.sub1,
                                        submitter_user=self.student3)

        last_by_after_change = self.re.last_reviews_by(self.student3) \
                                      .filter(reviewed_submission__submitter_user=self.student1).first()

        self.assertNotEqual(last_by_before_change, last_by_after_change)
        self.assertEqual(self.re.last_reviews_by(self.student3).count(), 2)

