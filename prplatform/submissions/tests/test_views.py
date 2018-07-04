from django.test import RequestFactory, TestCase

from prplatform.users.models import User
from prplatform.courses.models import Course
from prplatform.exercises.models import SubmissionExercise

from prplatform.submissions.models import OriginalSubmission
from prplatform.submissions.views import OriginalSubmissionListView


class SubmissionsTest(TestCase):
    fixtures = ["courses.yaml"]

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.kwargs = {'base_url_slug': 'prog1', 'url_slug': 'F2018'}

    def test_studentCanOnlyViewPersonalSubmissions(self):

        exercise = SubmissionExercise.objects.get(pk=1)
        course = Course.objects.get(pk=1)

        for username in ["student1", "student2", "student3"]:
            user = User.objects.get(username=username)
            OriginalSubmission(course=course, submitter=user, exercise=exercise, text="jadajada").save()

        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="student1")
        self.kwargs['pk'] = 1

        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)

        self.assertEqual(OriginalSubmission.objects.all().count(), 3)
        self.assertEqual(response.context_data['originalsubmission_list'].count(), 1)
        self.assertNotContains(response, "student2")  # hacky
        self.assertNotContains(response, "student3")

    def test_teacherCanViewAllSubmissions(self):

        exercise = SubmissionExercise.objects.get(pk=1)
        course = Course.objects.get(pk=1)

        for username in ["student1", "student2", "student3", "teacher1"]:
            user = User.objects.get(username=username)
            OriginalSubmission(course=course, submitter=user, exercise=exercise, text="jadajada").save()

        request = self.factory.get('/courses/prog1/F2018/submissions/s/1/list/')
        request.user = User.objects.get(username="teacher1")
        self.kwargs['pk'] = 1

        response = OriginalSubmissionListView.as_view()(request, **self.kwargs)

        self.assertEqual(OriginalSubmission.objects.all().count(), 4)
        self.assertEqual(response.context_data['originalsubmission_list'].count(), 4)
        self.assertContains(response, "student1")  # hacky
        self.assertContains(response, "student2")
        self.assertContains(response, "student3")
        self.assertContains(response, "teacher1")