from django.test import RequestFactory, TestCase

from prplatform.users.models import User
from prplatform.exercises.models import SubmissionExercise

from prplatform.courses.views import CourseDetailView


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
