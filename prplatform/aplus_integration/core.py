import requests
import os
import json

from django.core.cache import cache
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from prplatform.users.models import User
from prplatform.submissions.models import OriginalSubmission

import logging
logger = logging.getLogger(__name__)

def get_real_submission_from_hook_data(submission_exercise, query_dict):
    # <QueryDict: {'exercise_id': ['6'], 'site': ['http://localhost:8000'], 'submission_id': ['8'], 'course_id': ['1']}>

    site = query_dict.get('site')
    if 'localhost:8000' in site:
        site = 'http://172.17.0.1:9000'

    exercise_id = query_dict.get('exercise_id')
    submission_id = query_dict.get('submission_id')
    submission_url = f"{site}/api/v2/submissions/{submission_id}"
    AUTHENTICATION_HEADERS = {
        'Authorization': f"Token {submission_exercise.course.aplus_apikey}"
    }
    return requests.get(submission_url, headers=AUTHENTICATION_HEADERS).json()

def handle_submission_by_hook(apicall_request_object):
    submission_exercise = apicall_request_object.submission_exercise
    aplus_hook_data = apicall_request_object.hook_data

    submission_json = get_real_submission_from_hook_data(submission_exercise, aplus_hook_data)

    if submission_json['status'] == 'waiting':
        return (False, 'Not ready yet')

    grade = submission_json['grade']
    late_penalty = submission_json['late_penalty_applied']
    grading_data = submission_json['grading_data']

    if grading_data['points'] == grading_data['max_points']:
        logger.info("enough points received -> creating a submission")
        user = get_user(submission_json)
        create_submission_for(submission_exercise, submission_json, user)

    return (True, 'Handled, may be deleted')

def get_user(aplus_submission):

    submitter = aplus_submission["submitters"][0]
    email = submitter["email"]
    username = submitter["username"]

    try:
        user = User.objects.get(email=email, lti=True)

    except Exception as e:
        logger.info(e)
        logger.info(f"USER WAS NOT FOUND BY EMAIL {email} --> creating a new one")

        # prefixed username to not clash with shibboleth-based accounts
        user = User.objects.create_user(username=f"lti_{username}", email=email, lti=True)
        user.set_unusable_password()
        user.save()

    return user

def create_submission_for(submission_exercise, aplus_submission, user):
    """
       1. check if there's an user with the aplus submitter's email
       2. if not, crate one and set temporary = True
       3. get the submissions file from aplus API
       4. create a new original submission with the file and submitter
    """

    file_url = aplus_submission["files"][0]["url"]
    filename = aplus_submission["files"][0]["filename"]
    file_blob = requests.get(file_url, headers={ 'Authorization': f'Token {submission_exercise.course.aplus_apikey}' })

    temp_file = NamedTemporaryFile(delete=True)
    temp_file.name = filename
    temp_file.write(file_blob.content)
    temp_file.flush()

    new_orig_sub = OriginalSubmission(
                        course=submission_exercise.course,
                        submitter_user=user,
                        exercise=submission_exercise,
                        file=File(temp_file)
                        )
    new_orig_sub.save()
    logger.info(new_orig_sub)

