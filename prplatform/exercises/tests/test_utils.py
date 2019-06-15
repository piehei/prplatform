from django.test import TestCase

from prplatform.exercises.models import SubmissionExercise, ReviewExercise
from prplatform.exercises.utils import prepare_group_review_exercise_for
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
        g1 = StudentGroup(course=self.course, name='g1',
                          student_usernames=[self.student1.email, self.student2.email])
        g1.save()

        self.assertEqual(self.se.submissions.count(), 0)
        self.assertEqual(User.objects.filter(temporary=True).count(), 0)

        LTI_MODE = False

        user_count = User.objects.count()
        # no new students, submissions for all group members
        prepare_group_review_exercise_for(self.re, self.student1, LTI_MODE)
        self.assertEqual(self.se.submissions.count(), 2)
        self.assertEqual(User.objects.all().count(), user_count)
        # second call should not have any effect
        prepare_group_review_exercise_for(self.re, self.student2, LTI_MODE)
        self.assertEqual(self.se.submissions.count(), 2)
        self.assertEqual(User.objects.count(), user_count)

        new_student_email = 'new_student@example.com'
        g1.student_usernames += [new_student_email]
        g1.save()

        # should create one new temp user for new_student_email
        prepare_group_review_exercise_for(self.re, self.student2, LTI_MODE)
        self.assertEqual(self.se.submissions.count(), 3)
        new_student = User.objects.get(temporary=True, lti=LTI_MODE)
        self.assertEqual(new_student.username, f'temp-{new_student_email}')
        self.assertEqual(new_student.email, new_student_email)

        new_student.delete()
        self.assertEqual(self.se.submissions.count(), 2)

        # test user creation again, like above, but this time so that
        # the db allready has temporary user for that email *with LTI=Trye*
        # --> because the existing temp user has LTI=True and the required
        #     user should be LTI=False, new user should be created
        new_user_lti = User.objects.create(username='temp-lti-new_student@example.com',
                                           email=new_student_email,
                                           lti=True)

        user_count = User.objects.count()
        # should create one new temp user for new_student_email
        prepare_group_review_exercise_for(self.re, self.student2, LTI_MODE)
        self.assertEqual(self.se.submissions.count(), 3)
        new_student = User.objects.get(temporary=True, lti=LTI_MODE)
        self.assertEqual(new_student.username, f'temp-{new_student_email}')
        self.assertEqual(new_student.email, new_student_email)
        self.assertEqual(User.objects.count(), user_count + 1)

        # any further calls should have no effect
        user_count = User.objects.count()
        sub_count = self.se.submissions.count()
        for user in [self.student1, self.student2, new_student]:
            prepare_group_review_exercise_for(self.re, user, LTI_MODE)
            self.assertEqual(self.se.submissions.count(), sub_count)
            self.assertEqual(user_count, User.objects.count())

        LTI_MODE = True
        self.student1.lti = True
        self.student1.save()
        new_user_lti.delete()
        self.se.submissions.all().delete()
        # only student1 with lti=True from the group of student1, student2, news_student
        # exist ---> call with LTI_MODE=True should create two new users with temp=True
        #            and three submissions (one for each)
        user_count = User.objects.count()
        sub_count = self.se.submissions.count()
        prepare_group_review_exercise_for(self.re, self.student1, LTI_MODE)
        self.assertEqual(User.objects.count(), user_count + 2)
        new_lti_temp_users = User.objects.filter(lti=True, temporary=True)
        self.assertEqual(new_lti_temp_users.count(), 2)
        # usernames match what was expected
        new_usernames = [f'temp-lti-{u.email}' for u in new_lti_temp_users]
        self.assertEqual(User.objects.filter(username__in=new_usernames).count(), 2)
        self.assertEqual(self.se.submissions.count(), sub_count + 3)

        user_count = User.objects.count()
        sub_count = self.se.submissions.count()
        # should not create new users nor submissions
        for user in [self.student1, self.student2, new_student]:
            prepare_group_review_exercise_for(self.re, user, LTI_MODE)
            self.assertEqual(self.se.submissions.count(), sub_count)
            self.assertEqual(user_count, User.objects.count())
