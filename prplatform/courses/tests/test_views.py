from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase

from prplatform.users.models import User
from prplatform.exercises.models import SubmissionExercise

from prplatform.courses.views import CourseDetailView
from prplatform.submissions.views import OriginalSubmissionListView


class CoursesTest(TestCase):
    fixtures = ["courses.yaml"]

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.kwargs = {'base_url_slug': 'prog1', 'url_slug': 'F2018'}

    def test_studentDoesntSeeHiddenSubmissionExercises(self):

        request = self.factory.get('/courses/prog1/F2018/')
        request.user = User.objects.get(username="student1")

        response = CourseDetailView.as_view()(request, **self.kwargs)

        self.assertEqual(response.context_data['submissionexercises'].count(),
                         SubmissionExercise.objects.count())

        sub = SubmissionExercise.objects.get(name='T2 FILE')
        sub.visible_to_students = False
        sub.save()

        response = CourseDetailView.as_view()(request, **self.kwargs)

        self.assertEqual(response.context_data['submissionexercises'].count(),
                         SubmissionExercise.objects.count() - 1)

    def test_teacherSeesHiddenSubmissionExercises(self):

        request = self.factory.get('/courses/prog1/F2018/')
        request.user = User.objects.get(username="teacher1")

        response = CourseDetailView.as_view()(request, **self.kwargs)

        self.assertEqual(response.context_data['submissionexercises'].count(),
                         SubmissionExercise.objects.count())

        sub = SubmissionExercise.objects.get(name='T2 FILE')
        sub.visible_to_students = False
        sub.save()

        response = CourseDetailView.as_view()(request, **self.kwargs)

        self.assertEqual(response.context_data['submissionexercises'].count(),
                         SubmissionExercise.objects.count())

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

