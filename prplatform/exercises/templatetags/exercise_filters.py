from django import template

register = template.Library()


def my_submission_count(exercise, user):
    if exercise.use_groups:
        return exercise.submissions.filter(
                submitter_group=exercise.course.find_studentgroup_by_user(user)).count()
    return exercise.submissions.filter(submitter_user=user).count()


def my_received_feedback_count(exercise, user):
    if exercise.course.is_teacher(user):
        return 0
    return exercise.last_reviews_for(user).count()


register.filter('my_submission_count', my_submission_count)
register.filter('my_received_feedback_count', my_received_feedback_count)


