from django.http import HttpResponse
from django.views.generic import DetailView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import requests

from .models import AplusAPICallRequest

from prplatform.courses.views import (
        CourseContextMixin,
    )

from prplatform.exercises.models import SubmissionExercise
from prplatform.aplus_integration.core import (
        get_user,
        create_submission_for,
    )



@method_decorator(csrf_exempt, name='dispatch')
class ExerciseIncomingHook(CourseContextMixin, DetailView):

    model = SubmissionExercise

    def post(self, *args, **kwargs):
        self.object = None
        ctx = self.get_context_data(**kwargs)

        self.object = SubmissionExercise.objects.filter(
               course=ctx['course'],
               aplus_course_id=self.request.POST.get('course_id'),
               aplus_exercise_id=self.request.POST.get('exercise_id')
            ).first()

        if self.object:

            # this will be processed from a "queue" by a cron job in a separate
            # process handled by django mgmt commands
            AplusAPICallRequest.objects.create(
                    submission_exercise=self.object,
                    hook_data=self.request.POST)

        # just end the connection no matter what actually happened
        return HttpResponse("OK :-)")
