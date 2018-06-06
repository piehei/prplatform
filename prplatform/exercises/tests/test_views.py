

from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from prplatform.users.models import User
from prplatform.courses.models import BaseCourse, Course, Enrollment

from prplatform.exercises.views import SubmissionExerciseCreateView, SubmissionExerciseDetailView


class ExerciseTest(TestCase):
    fixtures = ["courses.yaml"]

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.kwargs = {'base_url_slug': 'prog1', 'url_slug': 'F2018', 'pk': 1}

    ###
    #   SubmissionExerciseCreateView
    #   uses isTeacherMixin
    #

    def test_isTeacher_anon_raises(self):

        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')

        request.user = AnonymousUser()
        self.assertRaises(PermissionDenied,
                          SubmissionExerciseCreateView.as_view(), request, **self.kwargs)

        request.user = User.objects.get(username="student1")
        self.assertRaises(PermissionDenied,
                          SubmissionExerciseCreateView.as_view(), request, **self.kwargs)

        request.user = User.objects.get(username="teacher1")
        try:
            SubmissionExerciseCreateView.as_view()(request, **self.kwargs)
        except Exception:
            self.fail("Teacher should be allowed to access")

    ###
    #   SubmissionExerciseDetailView
    #   uses isEnrolledMixin
    #

    def test_isEnrolled(self):

        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')

        request.user = AnonymousUser()
        self.assertRaises(PermissionDenied,
                          SubmissionExerciseDetailView.as_view(), request, **self.kwargs)

        request.user = User.objects.get(username="student1")
        try:
            SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        except Exception:
            self.fail("Student should be allowed to access")
