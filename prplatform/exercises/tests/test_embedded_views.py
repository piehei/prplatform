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
