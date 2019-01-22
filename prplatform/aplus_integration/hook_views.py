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


def get_submission_by_hook(submission_exercise, query_dict):
    # <QueryDict: {'exercise_id': ['6'], 'site': ['http://localhost:8000'], 'submission_id': ['8'], 'course_id': ['1']}>

    site = query_dict.get('site')
    if 'localhost:8000' in site:
        site = 'http://172.17.0.1:9000'

    exercise_id = query_dict.get('exercise_id')
    submission_id = query_dict.get('submission_id')


    submission_url = f"{site}/api/v2/submissions/{submission_id}"
    print("submission_url:", submission_url)

    AUTHENTICATION_HEADERS = {
        'Authorization': f"Token {submission_exercise.course.aplus_apikey}"
    }
    return requests.get(submission_url, headers=AUTHENTICATION_HEADERS).json()

def handle_submission(submission_exercise, aplus_submission):

    grade = aplus_submission['grade']
    late_penalty = aplus_submission['late_penalty_applied']
    grading_data = aplus_submission['grading_data']

    if grading_data['points'] == grading_data['max_points']:
        user = get_user(aplus_submission)
        create_submission_for(submission_exercise, aplus_submission, user)

    else:
        print("not enough points, skipping")


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

        if not self.object:
            print("This exercise is not configured for peer-reviews. Ignoring.")
            return HttpResponse('This will be ignored.')


        aplus_submission = get_submission_by_hook(self.object, self.request.POST)
        print(aplus_submission)

        if aplus_submission['status'] == 'waiting':
            print("STATUS IS: waiting ---> creating an api call request")
            AplusAPICallRequest.objects.create(
                    submission_exercise=self.object,
                    aplus_submission_data=aplus_submission)

        elif aplus_submission['status'] == 'ready':
            print("STATUS IS: ready -> handling")
            handle_submission(self.object, aplus_submission)

        return HttpResponse("OK :-)")
