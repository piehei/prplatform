from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from prplatform.exercises.deviation_models import SubmissionExerciseDeviation, ReviewExerciseDeviation
from prplatform.submissions.models import OriginalSubmission, ReviewSubmission
from prplatform.users.models import User


class ExerciseTestCase(TestCase):

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

    def create_originalsubmission_for(self, exercise, users):
        if type(users) is not list:
            users = [users]

        submissions = []
        for user in users:
            sub = OriginalSubmission(course=self.course,
                                     submitter_user=user,
                                     exercise=exercise,
                                     text=f"text by {user}")
            sub.save()
            submissions.append(sub)
        return submissions

    def create_reviewsubmission_for(self, exercise, reviewer=None, reviewed=None, osubmission=None, create_original=False):
        if osubmission and reviewer:
            return ReviewSubmission.objects.create(course=self.course, exercise=exercise, reviewed_submission=osubmission, submitter_user=reviewer)
        if reviewer and reviewed and not osubmission:
            if not create_original:
                osub_reviewed = exercise.reviewable_exercise.submissions_by_submitter(reviewed).first()
                if not osub_reviewed:
                    raise Exception("OriginalSubmission not found but create_original=False")
            else:
                osub_reviewed = self.create_originalsubmission_for(
                    exercise.reviewable_exercise, reviewed)[0]
            return osub_reviewed, ReviewSubmission.objects.create(course=self.course, exercise=exercise, reviewed_submission=osub_reviewed, submitter_user=reviewer)

    def test_last_submission_by_submitters(self):

        self.create_originalsubmission_for(self.se, [self.student1, self.student2])

        last_subs = self.se.last_submission_by_submitters()
        self.assertEqual(last_subs.count(), 2)
        self.assertNotEqual(last_subs[0].submitter_user, last_subs[1].submitter_user)

        sub_s1_2, sub_s2_2 = self.create_originalsubmission_for(self.se, [self.student1, self.student2])
        last_subs_again = self.se.last_submission_by_submitters()
        self.assertEqual(last_subs_again.count(), 2)

        self.assertNotEqual(last_subs.filter(submitter_user=self.student1),
                            last_subs_again.filter(submitter_user=self.student1))
        self.assertNotEqual(last_subs.filter(submitter_user=self.student2),
                            last_subs_again.filter(submitter_user=self.student2))
        self.assertEqual(sub_s1_2 in last_subs_again, True)
        self.assertEqual(sub_s2_2 in last_subs_again, True)

    def test_last_reviews_for(self):

        student1_osub, _ = self.create_reviewsubmission_for(
            self.re, reviewed=self.student1, reviewer=self.student2, create_original=True)
        self.create_reviewsubmission_for(self.re, reviewer=self.student3, osubmission=student1_osub)
        self.create_reviewsubmission_for(self.re, reviewer=self.student3, reviewed=self.student2, create_original=True)

        self.assertEqual(self.re.last_reviews_for(self.student1).count(), 2)
        self.assertEqual(self.re.last_reviews_for(self.student2).count(), 1)

        review_by_s3 = self.re.last_reviews_for(self.student1).filter(submitter_user=self.student3).first()

        self.create_reviewsubmission_for(self.re, reviewer=self.student3, osubmission=student1_osub)

        review_by_s3_new = self.re.last_reviews_for(self.student1).filter(submitter_user=self.student3).first()
        self.assertNotEqual(review_by_s3, review_by_s3_new)
        self.assertEqual(self.re.last_reviews_for(self.student1).count(), 2)

    def test_last_reviews_by(self):

        osub_student1, * \
            _ = self.create_reviewsubmission_for(self.re, reviewer=self.student2,
                                                 reviewed=self.student1, create_original=True)
        self.create_reviewsubmission_for(self.re, reviewer=self.student3, osubmission=osub_student1)
        self.create_reviewsubmission_for(self.re, reviewer=self.student3, reviewed=self.student2, create_original=True)
        self.assertEqual(self.re.last_reviews_by(self.student1).count(), 0)
        self.assertEqual(self.re.last_reviews_by(self.student2).count(), 1)
        self.assertEqual(self.re.last_reviews_by(self.student3).count(), 2)

        review_by_student3 = self.re.last_reviews_by(self.student3) \
            .filter(reviewed_submission__submitter_user=self.student1).first()

        self.create_reviewsubmission_for(self.re, reviewer=self.student3, osubmission=osub_student1)

        review_by_student3_new = self.re.last_reviews_by(self.student3) \
            .filter(reviewed_submission__submitter_user=self.student1).first()

        self.assertNotEqual(review_by_student3, review_by_student3_new)
        self.assertEqual(self.re.last_reviews_by(self.student3).count(), 2)

    def test_submissionexercise_can_submit(self):
        self.assertEqual(self.se.can_submit(AnonymousUser()), False)

        self.student1.enrollments.all().delete()
        self.assertEqual(self.se.can_submit(self.student1), False)

        self.se.use_groups = True
        self.se.save()
        self.assertEqual(self.se.can_submit(self.student2), False)
        self.se.use_groups = False
        self.se.save()

        self.se.opening_time = timezone.now()+timezone.timedelta(hours=1)
        self.se.closing_time = timezone.now()+timezone.timedelta(hours=2)
        self.se.save()
        self.assertEqual(self.se.can_submit(self.student2), False)

        self.se.opening_time = timezone.now()-timezone.timedelta(hours=2)
        self.se.closing_time = timezone.now()-timezone.timedelta(hours=1)
        self.se.save()
        self.assertEqual(self.se.can_submit(self.student2), False)

        SubmissionExerciseDeviation(user=self.student2, exercise=self.se,
                                    new_deadline=timezone.now()+timezone.timedelta(hours=10)).save()
        self.assertEqual(self.se.can_submit(self.student2), True)

    def test_reviewexercise_can_submit(self):
        self.assertEqual(self.re.can_submit(AnonymousUser()), (False, None))

        self.student1.enrollments.all().delete()
        self.assertEqual(self.re.can_submit(self.student1), (False, None))

        self.assertEqual(self.re.can_submit(self.student2), (False, 'own_submission_missing'))
        self.create_originalsubmission_for(self.se, self.student2)
        self.assertEqual(self.re.can_submit(self.student2), (True, None))

        _, rsub = self.create_reviewsubmission_for(
            self.re, reviewer=self.student2, reviewed=self.student1, create_original=True)
        self.assertEqual(self.re.can_submit(self.student2), (False, 'reviews_done'))

        rsub.delete()

        self.re.use_groups = True
        self.re.save()
        self.assertEqual(self.re.can_submit(self.student2), (False, None))
