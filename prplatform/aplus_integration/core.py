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

# will be replaced with api key set for the course
HEADERS = {'Authorization': 'Token xxx'}

# TODO: dirty hack, replace with something like reading json conf or whatnot
#       in early dev phase this is used to test against production aplus
#       installation -> some student emails will be replaced with madeup ones
REPLACE = {}
if os.environ.get('REPLACE'):
    REPLACE = json.loads(os.environ.get('REPLACE'))


def get_submissions(submission_exercise):
    # TODO: REFACTOR COMPLETELY
    return


    """
        1. retrieve submissions to this exercise from aplus api
        2. if teacher has not set api key to the course, return err
        3. use only submissions whose submitter's emails are in REPLACE
        4. create orig submissions for each of them by calling create_submission
    """
    exercise_id = submission_exercise.aplus_exercise_id

    HEADERS['Authorization'] = f"Token {submission_exercise.course.aplus_apikey}"

    results = cache.get(exercise_id)
    if not results:
        try:
            results = []

            url_next = f"https://plus.cs.tut.fi/api/v2/exercises/{exercise_id}/submissions/"
            while url_next:
                logger.info(url_next)
                resp = requests.get(url_next, headers=HEADERS)
                data = resp.json()
                results = results + data["results"]
                # this will be None when there's no additional pages of 100 results
                url_next = data["next"]

        except Exception as e:
            logger.error(e)
            logger.error8(e.text)
            return False

        # cache.set(exercise_id, results, 60 * 5)

    users_and_ids = {}
    users_and_submissions = {}

    logger.info(f"length of results is {len(results)} --> getting them one by one")
    for result in results:

        submission = cache.get(result['id'])
        if not submission:
            submission = requests.get(result["url"], headers=HEADERS).json()
            cache.set(result['id'], submission, 60 * 5)

        submitter_email = submission["submitters"][0]["email"]

        # if submitter_email not in REPLACE:
        #     continue

        if submitter_email in REPLACE:
            logger.info(f"replacing: {submitter_email} -> {REPLACE[submitter_email]}")
            submitter_email = REPLACE[submitter_email]
            submission["submitters"][0]["email"] = submitter_email

        if submitter_email not in users_and_ids:
            users_and_ids[submitter_email] = []
        users_and_ids[submitter_email].append(result["id"])

        if submitter_email not in users_and_submissions:
            users_and_submissions[submitter_email] = submission

    logger.info("These will be added:")
    logger.info(users_and_ids)

    created_users = 0
    created_submissions = 0

    for user in users_and_submissions:
        if create_user(users_and_submissions[user]):
            created_users += 1

        if create_submission_for(submission_exercise, users_and_submissions[user]):
            created_submissions += 1

    logger.info(f"Created {created_users} new users")
    logger.info(f"Created {created_submissions} new submissions")

    return True


def get_user(aplus_submission):

    submitter = aplus_submission["submitters"][0]
    email = submitter["email"]
    username = submitter["username"]

    try:
        user = User.objects.get(email=email)

    except Exception as e:
        logger.info(e)
        logger.info(f"USER WAS NOT FOUND BY EMAIL {email} --> creating a new one")

        user = User.objects.create_user(username=username, email=email)
        user.set_unusable_password()
        user.temporary = True
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

