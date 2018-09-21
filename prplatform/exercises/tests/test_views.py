from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.test import RequestFactory, TestCase

from prplatform.users.models import User
from prplatform.courses.models import Course
from prplatform.submissions.models import OriginalSubmission

from prplatform.exercises.views import SubmissionExerciseCreateView, SubmissionExerciseDetailView
from prplatform.exercises.models import SubmissionExercise


def add_middleware(request, middleware_class):
    middleware = middleware_class()
    middleware.process_request(request)
    return request


class ExerciseTest(TestCase):
    fixtures = ["courses.yaml"]

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.kwargs = {'base_url_slug': 'prog1', 'url_slug': 'F2018'}

    ###
    #   SubmissionExerciseCreateView
    #   uses isTeacherMixin
    #

    def test_isTeacher_anon_raises(self):

        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')
        self.kwargs['pk'] = 1
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
        self.kwargs['pk'] = 1

        request.user = AnonymousUser()
        self.assertRaises(PermissionDenied,
                          SubmissionExerciseDetailView.as_view(), request, **self.kwargs)

        request.user = User.objects.get(username="student1")
        try:
            SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        except Exception:
            self.fail("Student should be allowed to access")

    def test_exerciseOpen(self):

        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')
        request.user = User.objects.get(username="student1")
        self.kwargs['pk'] = 1

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)

        self.assertNotContains(response, "This exercise is closed.")
        self.assertContains(response, "Submit")
        self.assertContains(response, "<form")

    def test_exerciseClosed(self):

        request = self.factory.get('/courses/prog1/F2018/exercises/s/4/')
        request.user = User.objects.get(username="student1")
        self.kwargs['pk'] = 4

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertContains(response, "This exercise is closed.")
        self.assertEqual(response.context_data['disable_form'], True)

    def test_studentCanSubmit(self):

        request = self.factory.post('/courses/prog1/F2018/exercises/s/1/', {'text': 'Submitted text'})
        request.user = User.objects.get(username="student1")
        self.kwargs['pk'] = 1

        request = add_middleware(request, SessionMiddleware)
        request = add_middleware(request, MessageMiddleware)

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)
        self.assertEqual(response.status_code, 302)

    def test_studentCannotSubmitMultipleTimes(self):

        # first create a submission by a student
        user = User.objects.get(username="student1")
        exercise = SubmissionExercise.objects.get(pk=1)
        course = Course.objects.get(pk=1)
        OriginalSubmission(course=course, submitter_user=user, exercise=exercise, text="jadajada").save()
        # then load the page and check it disables second submission
        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')
        request.user = user
        self.kwargs['pk'] = 1

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)

        self.assertContains(response, "You have reached the maximum number of submissions")
        self.assertEqual(response.context_data['disable_form'], True)

    def test_teacherCanSubmitMultipleTimes(self):

        user = User.objects.get(username="teacher1")
        exercise = SubmissionExercise.objects.get(pk=1)
        course = Course.objects.get(pk=1)
        OriginalSubmission(course=course, submitter_user=user, exercise=exercise, text="jadajada").save()
        OriginalSubmission(course=course, submitter_user=user, exercise=exercise, text="jadajada").save()
        OriginalSubmission(course=course, submitter_user=user, exercise=exercise, text="jadajada").save()

        request = self.factory.get('/courses/prog1/F2018/exercises/s/1/')
        request.user = user
        self.kwargs['pk'] = 1

        response = SubmissionExerciseDetailView.as_view()(request, **self.kwargs)

        self.assertNotContains(response, "You have reached the maximum number of submissions.")
        self.assertContains(response, "Submit")
