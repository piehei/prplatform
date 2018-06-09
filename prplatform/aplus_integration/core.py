import requests
import os
import json

from django.core.cache import cache
from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

from prplatform.users.models import User
from prplatform.submissions.models import OriginalSubmission

# will be replaced with api key set for the course
HEADERS = {'Authorization': 'Token xxx'}

# TODO: dirty hack, replace with something like reading json conf or whatnot
#       in early dev phase this is used to test against production aplus
#       installation -> some student emails will be replaced with madeup ones
REPLACE = {}
if os.environ.get('REPLACE'):
    REPLACE = json.loads(os.environ.get('REPLACE'))


def get_submissions_by_id(submission_exercise):
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
            resp = requests.get(f"https://plus.cs.tut.fi/api/v2/exercises/{exercise_id}/submissions/",
                                headers=HEADERS)

            results = resp.json()["results"]
        except Exception as e:
            print(e)
            print(resp.text)
            return str(e)

        cache.set(exercise_id, results, 60 * 5)

    users_and_ids = {}
    users_and_submissions = {}

    print(f"length of results is {len(results)} --> getting them one by one")
    for result in results:

        submission = cache.get(result['id'])
        if not submission:
            submission = requests.get(result["url"], headers=HEADERS).json()
            cache.set(result['id'], submission, 60 * 5)

        submitter_email = submission["submitters"][0]["email"]

        if submitter_email not in REPLACE:
            continue

        print(f"replacing: {submitter_email} -> {REPLACE[submitter_email]}")
        submitter_email = REPLACE[submitter_email]
        submission["submitters"][0]["email"] = submitter_email

        if submitter_email not in users_and_ids:
            users_and_ids[submitter_email] = []
        users_and_ids[submitter_email].append(result["id"])

        if submitter_email not in users_and_submissions:
            users_and_submissions[submitter_email] = submission

    print(users_and_ids)

    for user in users_and_submissions:
        create_submission(submission_exercise, users_and_submissions[user])


def create_submission(submission_exercise, aplus_submission):
    """
       1. check if there's an user with the aplus submitter's email
       2. if not, crate one and set is_active = False
       3. get the submissions file from aplus API
       4. create a new original submission with the file and submitter
    """

    print("create submission")

    email = aplus_submission["submitters"][0]["email"]
    try:
        user = User.objects.get(email=email)
    except Exception as e:
        print(e)
        print(f"USER WAS NOT FOUND BY EMAIL {email}")

        user = User.objects.create_user(email, email, '')
        user.set_unusable_password()
        user.is_active = False
        user.save()

    if len(submission_exercise.submissions.filter(submitter=user)) > 0:
        print("skipping this submission from aplus api -> the user already has one origsub")
        return

    file_url = aplus_submission["files"][0]["url"]
    file_blob = requests.get(file_url, headers=HEADERS)

    temp_file = NamedTemporaryFile(delete=True)
    temp_file.write(file_blob.content)
    temp_file.flush()

    new_orig_sub = OriginalSubmission(
                        course=submission_exercise.course,
                        submitter=user,
                        exercise=submission_exercise,
                        file=File(temp_file)
                        )
    new_orig_sub.save()

    print(new_orig_sub)
