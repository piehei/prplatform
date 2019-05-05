import logging

from prplatform.users.models import User
from prplatform.submissions.models import OriginalSubmission
from prplatform.courses.utils import get_email_candidates

logger = logging.getLogger('exercise.utils')


def prepare_group_review_exercise_for(exercise, user):
    """
    This is called just before showing the student a group peer-review
    page where the student can peer-review other students in his/her group.

    Because of the design of the system, there has to exist an OriginalSubmission
    for each ReviewSubmission. This function will do two things:

    1. if the receiver of the feedback (student in the same group) has never
       logged into the system (and thus his/her account doesn't exist yet),
       a new temporary user account with his/her email will be created

    2. create one OriginalSubmission for each of the group members so that
       the peer-reviews  (ReviewSubmissions) can point to them

    About point 1: when the user logs in in the future via Shibboleth (or so),
                   this temporary account will be removed and all submissions
                   transerred to the actual, real user account (users/receivers.py)
    """

    course = exercise.course
    group = course.find_studentgroup_by_user(user)

    if not group:
        return

    for student_email in group.student_usernames:

        candidates = get_email_candidates(student_email)
        # first matching student who is preferably NOT temporary
        student = User.objects.filter(email__in=candidates).order_by('temporary').first()

        if not student:
            logger.info(f'ReviewExericse (pk={exercise.pk}): User not found for {candidates} -> creating temp user in perpare_group_review_exercise_for')
            student = User(username=f"temp-{student_email}",
                           email=student_email,
                           temporary=True)
            student.save()

        prev_sub = exercise.reviewable_exercise.submissions.filter(
                                                submitter_user=student,
                                               ).first()

        if not prev_sub:
            osub = OriginalSubmission(
                        course=course,
                        exercise=exercise.reviewable_exercise,
                        submitter_user=student,
                        text=("This is *automatically* created submission for group peer-review. "
                              "This is needed because every peer-review has to point to some original "
                              "submission.")
                    )
            osub.save()
