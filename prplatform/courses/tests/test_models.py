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
        g1 = StudentGroup.objects.create(course=course,
                                         name="g1",
                                         student_usernames=[s1.email])

        self.assertEqual(course.find_studentgroup_by_user(s1), g1)
        self.assertEqual(course.find_studentgroup_by_user(s2), None)

        g1.student_usernames += [s2.email]
        g1.save()
        self.assertEqual(course.find_studentgroup_by_user(s1), g1)
        self.assertEqual(course.find_studentgroup_by_user(s2), g1)

        g1.student_usernames = []
        g1.save()
        self.assertEqual(course.find_studentgroup_by_user(s1), None)
        self.assertEqual(course.find_studentgroup_by_user(s2), None)
        self.assertEqual(course.find_studentgroup_by_user(AnonymousUser()), None)
