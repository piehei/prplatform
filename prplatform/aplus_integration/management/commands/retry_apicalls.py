
from django.core.management.base import BaseCommand

from prplatform.exercises.models import SubmissionExercise

from prplatform.aplus_integration.models import AplusAPICallRequest
from prplatform.aplus_integration.hook_views import (
        handle_submission,
    )

import requests

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetches all submissions to all APLUS SubmissionExercises'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        pending_calls = AplusAPICallRequest.objects.all()

        print(f"Found {pending_calls.count()} AplusAPICallRequests ---> fetch now")

        for call in pending_calls:
            try:
                print(f"Starting to handle {call}")
                url = call.aplus_submission_data['url']
                print("submission api url is:", url)
                json = requests.get(url, headers={ 'Authorization': f'Token {call.submission_exercise.course.aplus_apikey}' }).json()
                print(json)
                status = json['status']

                if status == 'waiting':
                    print("status waiting")
                    continue

                if status == 'ready' or status == 'unofficial':
                    print("status ready or unofficial")
                    handle_submission(call.submission_exercise, json)
                    print("handled --> deleting")
                    call.delete()
            except Exception as e:
                print(e)


