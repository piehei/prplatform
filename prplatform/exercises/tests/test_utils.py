from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser

from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from prplatform.exercises.utils import prepare_group_review_exercise_for
from prplatform.submissions.models import OriginalSubmission, ReviewSubmission
from prplatform.users.models import User, StudentGroup


class ExerciseUtilsTestCase(TestCase):

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

    def test_prepare_group_review_exercise_for(self):
        g1 = StudentGroup(course=self.course, name='g1', student_usernames=[self.student1.email, self.student2.email])
        g1.save()

        self.assertEqual(self.se.submissions.count(), 0)
        self.assertEqual(User.objects.filter(temporary=True).count(), 0)

        # should not create temp users, only submissions
        prepare_group_review_exercise_for(self.re, self.student1)
        self.assertEqual(self.se.submissions.count(), 2)
        prepare_group_review_exercise_for(self.re, self.student2)
        self.assertEqual(self.se.submissions.count(), 2)
        self.assertEqual(User.objects.filter(temporary=True).count(), 0)

        new_student_email = 'new_student@example.com'
        g1.student_usernames += [new_student_email]
        g1.save()
        prepare_group_review_exercise_for(self.re, self.student2)
        self.assertEqual(self.se.submissions.count(), 3)
        new_student = User.objects.get(temporary=True)  # this throws if count != 1
        self.assertEqual(new_student.username, f'temp-{new_student_email}')
        self.assertEqual(new_student.email, new_student_email)

        # now there's a temp user with email new_student@example.com
        # this user should be found if the domain of an email doesn't match but
        # courses.utils.get_email_candidates returns matching candidates
        g1.student_usernames.pop()
        second_new_student_email = 'new_student@something_else.com'
        g1.student_usernames += [second_new_student_email]
        g1.save()

        # --> no new temp user nor submissions should be created
        with self.settings(ADDITIONAL_GROUP_EMAIL_MATCHING_DOMAINS=['example.com']):
            prepare_group_review_exercise_for(self.re, self.student2)
            self.assertEqual(self.se.submissions.count(), 3)
            new_student = User.objects.get(temporary=True)  # this throws if count != 1
            self.assertEqual(new_student.username, f'temp-{new_student_email}')
            self.assertEqual(new_student.email, new_student_email)

        # this should create a new temp user since matching domains are not used
        prepare_group_review_exercise_for(self.re, self.student2)
        self.assertEqual(self.se.submissions.count(), 4)
        new_student = User.objects.get(
            temporary=True, username=f'temp-{second_new_student_email}', email=second_new_student_email)
