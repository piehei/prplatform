from django.contrib.auth.models import AnonymousUser

from test_plus.test import TestCase

from prplatform.courses.models import Course
from prplatform.users.models import User, StudentGroup


class TestCourse(TestCase):

    fixtures = [
        'courses.yaml'
    ]

    def test_find_studentgroup_by_user(self):
        course = Course.objects.get(pk=1)
        s1 = User.objects.get(username="student1")
        s2 = User.objects.get(username="student2")

        # group file matches user email
        s1.email = "s1@ex1.com"
        s1.save()
        g1 = StudentGroup.objects.create(course=course,
                                         name="g1",
                                         student_usernames=[s1.email])
        self.assertEqual(course.find_studentgroup_by_user(s1), g1)

        # group file doesnt match user email
        g1.student_usernames = ["s1@ex2.com"]
        g1.save()
        self.assertEqual(course.find_studentgroup_by_user(s1), None)

        # group file doesnt match user email BUT system has been configured
        # to accept all emails in the group file + their variations with
        # configured domains
        # ---> matches s1@ex1.com and s1@ex2.com
        with self.settings(ADDITIONAL_GROUP_EMAIL_MATCHING_DOMAINS=['ex2.com']):
            self.assertEqual(course.find_studentgroup_by_user(s1), g1)

        self.assertEqual(course.find_studentgroup_by_user(AnonymousUser()), None)
        self.assertEqual(course.find_studentgroup_by_user(s2), None)
