import logging

from prplatform.users.models import User
from prplatform.submissions.models import OriginalSubmission

logger = logging.getLogger('exercise.utils')


def prepare_group_review_exercise_for(exercise, user, LTI_MODE):
    """
    This is called just before showing the student a group peer-review
    page where the student can peer-review other students in his/her group.

    Because of the design of the system, there has to exist an OriginalSubmission
    for each ReviewSubmission. This function will do two things:

    1. if the receiver of the feedback (student in the same group) has never
       logged into the system (and thus his/her account doesn't exist yet),
       a new temporary user account with his/her email will be created.
       for that new temp user account, temporary=True will be set.
       if the current user is using the system through LTI integration,
       lti=True will also be set since all users of a particular course
       either use the system through LTI or don't. this distinction makes it
       possible for a user to be attending two courses of which one uses
       LTI and one doesn't and the user accounts don't mix mistakenly.

    2. create one OriginalSubmission for each of the group members so that
       the peer-reviews  (ReviewSubmissions) can point to them

    3. when the real user logins in the future, this temporary account will be
       removed and all submissions transerred to the actual, real user account.
       this logic is implemented in prplatform.users.receivers
    """

    course = exercise.course
    group = course.find_studentgroup_by_user(user)

    if not group:
        return

    for student_email in group.student_usernames:
        logger.info(f"FINDING: {student_email}, LTI_MODE: {LTI_MODE}")
        student = User.objects.filter(email=student_email, lti=LTI_MODE).first()

        if not student:
            logger.info(f'ReviewExericse (pk={exercise.pk}): User not found for {student_email} '
                        f'(lti={LTI_MODE}) -> creating temp user in perpare_group_review_exercise_for')
            # temp_str distinguishes temp users created through LTI and outside of it
            # for the username is a unique field
            temp_str = 'lti-' if LTI_MODE else ''
            student = User(username=f"temp-{temp_str}{student_email}",
                           email=student_email,
                           lti=LTI_MODE,
                           temporary=True)
            student.save()

        if exercise.reviewable_exercise.submissions \
                                       .filter(submitter_user=student).exists():
            logger.info(f'Prev sub found for {student} --> not creating new')
        else:
            logger.info(f'Prev sub NOT FOUND for {student} --> creating new')
            osub = OriginalSubmission(
                course=course,
                exercise=exercise.reviewable_exercise,
                submitter_user=student,
                text=("This is *automatically* created submission for group peer-review. "
                      "This is needed because every peer-review has to point to some original "
                      "submission.")
            )
            osub.save()
