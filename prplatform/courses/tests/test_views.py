from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from prplatform.users.models import User
from prplatform.exercises.models import SubmissionExercise, ReviewExercise

from prplatform.courses.models import Course
from prplatform.courses.views import CourseDetailView, CourseListView
from prplatform.submissions.views import OriginalSubmissionListView


class CoursesTest(TestCase):
    fixtures = ["courses.yaml"]

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.kwargs = {'base_url_slug': 'prog1', 'url_slug': 'F2018'}

    def test_hiddenCourseIsHidden(self):

        course = Course.objects.first()
        course.hidden = True
        course.save()

        # course list
        request = self.factory.get('/courses/')

        request.user = User.objects.get(username="student1")

        response = CourseListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 0)

        request.user = User.objects.get(username="teacher1")

        response = CourseListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 1)

        # course page
        request = self.factory.get('/courses/prog1/F2018/')
        request.user = User.objects.get(username="student1")

        self.assertRaises(PermissionDenied,
                          CourseDetailView.as_view(), request, **self.kwargs)

        request.user = User.objects.get(username="teacher1")
        try:
            CourseDetailView.as_view()(request, **self.kwargs)
        except Exception:
            self.fail("Teacher should be allowed to access a hidden course")

        # make course visible
        course.hidden = False
        course.save()

        # course list
        request = self.factory.get('/courses/')
        request.user = User.objects.get(username="student1")

        response = CourseListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 1)

        request.user = User.objects.get(username="teacher1")
        response = CourseListView.as_view()(request, **self.kwargs)
        self.assertEqual(response.context_data['object_list'].count(), 1)

        # course page
        request = self.factory.get('/courses/prog1/F2018/')
        request.user = User.objects.get(username="student1")

        try:
            CourseDetailView.as_view()(request, **self.kwargs)
        except Exception:
            self.fail("Student should be allowed to access")

    def test_exerciseVisibilitySettingsWork(self):

        request = self.factory.get('/courses/prog1/F2018/')

        request.user = User.objects.get(username="student1")
        response = CourseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, 'T2 FILE SUBMISSION')
        self.assertContains(response, 'T2 FILE REVIEW')

        request.user = User.objects.get(username="teacher1")
        response = CourseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, 'T2 FILE SUBMISSION')
        self.assertContains(response, 'T2 FILE REVIEW')

        sub = SubmissionExercise.objects.get(name='T2 FILE SUBMISSION')
        sub.visible_to_students = False
        sub.save()

        request.user = User.objects.get(username="student1")
        response = CourseDetailView.as_view()(request, **self.kwargs)
        self.assertNotContains(response, 'T2 FILE SUBMISSION')
        self.assertContains(response, 'T2 FILE REVIEW')

        request.user = User.objects.get(username="teacher1")
        response = CourseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, 'T2 FILE SUBMISSION')
        self.assertContains(response, 'T2 FILE REVIEW')

        sub = ReviewExercise.objects.get(name='T2 FILE REVIEW')
        sub.visible_to_students = False
        sub.save()

        request.user = User.objects.get(username="student1")
        response = CourseDetailView.as_view()(request, **self.kwargs)
        self.assertNotContains(response, 'T2 FILE SUBMISSION')
        self.assertNotContains(response, 'T2 FILE REVIEW')

        request.user = User.objects.get(username="teacher1")
        response = CourseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, 'T2 FILE SUBMISSION')
        self.assertContains(response, 'T2 FILE REVIEW')

    def test_isEnrolled(self):

        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        self.kwargs['pk'] = 1

        request.user = AnonymousUser()
        self.assertRaises(PermissionDenied,
                          OriginalSubmissionListView.as_view(), request, **self.kwargs)

        request.user = User.objects.create(username="not_enrolled_user", email="d@d.fi")
        self.assertRaises(PermissionDenied,
                          OriginalSubmissionListView.as_view(), request, **self.kwargs)

        request.user = User.objects.get(username="student1")
        try:
            OriginalSubmissionListView.as_view()(request, **self.kwargs)
        except Exception:
            self.fail("Student should be allowed to access")

