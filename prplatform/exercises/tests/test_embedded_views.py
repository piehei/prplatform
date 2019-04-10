from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import AnonymousUser
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware
from django.test import RequestFactory, TestCase

import datetime
import pytz

from prplatform.users.models import (
        StudentGroup,
        User,
    )
from prplatform.courses.models import Course

from prplatform.submissions.models import (
        OriginalSubmission,
        ReviewSubmission,
    )
from prplatform.submissions.reviewlock_models import ReviewLock
from prplatform.submissions.views import ReviewSubmissionListView
from prplatform.exercises.views import (
        SubmissionExerciseCreateView,
        SubmissionExerciseDetailView,
        ReviewExerciseDetailView,
    )
from prplatform.exercises.models import (
        ReviewExercise,
        SubmissionExercise,
    )
from prplatform.exercises.deviation_models import SubmissionExerciseDeviation


def add_middleware(request, middleware_class):
    middleware = middleware_class()
    middleware.process_request(request)
    return request


def add_required_middlewares(request):
    request = add_middleware(request, SessionMiddleware)
    request = add_middleware(request, MessageMiddleware)
    # this is for LtiLoginMiddleware
    # TODO: should this be refactored somehow?
    request.LTI_MODE = False
    return request


class ExerciseEmbeddedTest(TestCase):
    fixtures = ["courses.yaml"]

    def setUp(self):
        # Every test needs access to the request factory.
        self.factory = RequestFactory()
        self.kwargs = {'base_url_slug': 'prog1', 'url_slug': 'F2018'}

        self.s1 = User.objects.get(username="student1")
        self.s2 = User.objects.get(username="student2")
        self.s3 = User.objects.get(username="student3")
        self.s4 = User.objects.get(username="student4")
        self.s5 = User.objects.get(username="student5")
        self.s6 = User.objects.get(username="student6")

        # dont add s5 and s6 here since tests were written before they existed
        self.students = [self.s1, self.s2, self.s3, self.s4]

        self.t1 = User.objects.get(username="teacher1")
        self.course = Course.objects.get(pk=1)
        self.se1 = SubmissionExercise.objects.get(name='T1 TEXT')
        self.re1 = ReviewExercise.objects.get(name='T1 TEXT REVIEW')

    def post(self, exercise, user, payload):

        request = self.factory.post(exercise.get_absolute_url(), payload)
        request.user = user
        self.kwargs['pk'] = exercise.pk
        request = add_required_middlewares(request)
        request.LTI_MODE = True
        views = {
            'SubmissionExercise': SubmissionExerciseDetailView,
            'ReviewExercise': ReviewExerciseDetailView,
        }
        name = exercise.__class__.__name__
        return views[name].as_view()(request, **self.kwargs)

    def get(self, exercise, user):

        request = self.factory.get(exercise.get_absolute_url())
        request.user = user
        request.LTI_MODE = True
        self.kwargs['pk'] = exercise.pk

        views = {
            'SubmissionExercise': SubmissionExerciseDetailView,
            'ReviewExercise': ReviewExerciseDetailView,
        }
        name = exercise.__class__.__name__
        return views[name].as_view()(request, **self.kwargs)

    def create_submission_for(self, exercise, users):

        submissions = []
        for user in users:
            sub = OriginalSubmission(course=self.course,
                                     submitter_user=user,
                                     exercise=exercise,
                                     text=f"text by {user}")
            sub.save()
            submissions.append(sub)
        return submissions

    def test_embedded_templates_used(self):

        views = [
            (SubmissionExercise.objects.get(name='T1 TEXT'), SubmissionExerciseDetailView),
            (ReviewExercise.objects.get(name='T1 TEXT REVIEW'), ReviewExerciseDetailView),
        ]
        for exercise, view in views:
            request = self.factory.get(exercise.get_absolute_url())
            request.user = self.s1
            self.kwargs['pk'] = 1
            response = view.as_view()(request, **self.kwargs)
            # BASE_EMBEDDED is inlined in templates/base_embedded.html
            self.assertNotContains(response, 'BASE_EMBEDDED')

            request = self.factory.get(exercise.get_absolute_url())
            request.user = self.s1
            self.kwargs['pk'] = 1
            response = view.as_view()(request, **self.kwargs)
            request.LTI_MODE = True
            response = view.as_view()(request, **self.kwargs)
            self.assertContains(response, 'BASE_EMBEDDED')

    def test_submissionexercise_response_constructed_correctly(self):

        se = SubmissionExercise.objects.get(name='T1 TEXT')

        res = self.post(se, self.s1, {'broken': 'form'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content.decode('utf-8'), 'An error occurred.')

        res = self.post(se, self.s1, {'text': 'text value'})
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertEqual('name="max-points" value="1"' in content, True)
        self.assertEqual('name="points" value="1"' in content, True)
        self.assertEqual('Submission received!' in content, True)

    def test_reviewexercise_response_constructed_correctly(self):

        self.create_submission_for(self.se1, [self.s1, self.s2])

        self.re1.require_original_submission = False
        self.re1.max_submission_count = 3
        self.re1.min_submission_count = 2
        self.re1.save()

        self.get(self.re1, self.s3)
        self.assertEqual(ReviewLock.objects.count(), 1)
        res = self.post(self.re1, self.s3, {'broken': 'form'})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content.decode('utf-8'), 'An error occurred.')

        answers = {
            'Q-PREFIX-2--question': ['2'],
            'Q-PREFIX-2--value_choice': ['1'],
            'Q-PREFIX-1--question': ['1'],
            'Q-PREFIX-1--value_text': ['some text']
        }

        res = self.post(self.re1, self.s3, answers)
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertEqual('name="max-points" value="1"' in content, True)
        self.assertEqual('name="points" value="0"' in content, True)
        self.assertEqual('Completed peer-review 1/2' in content, True)

        self.get(self.re1, self.s3)
        self.assertEqual(ReviewLock.objects.count(), 1)

        res = self.post(self.re1, self.s3, answers)
        self.assertEqual(res.status_code, 200)
        content = res.content.decode('utf-8')
        self.assertEqual('name="max-points" value="1"' in content, True)
        self.assertEqual('name="points" value="1"' in content, True)
        self.assertEqual('Completed peer-review 2/2' in content, True)
        self.assertEqual('You can do more peer-reviews if you want!' in content, True)
