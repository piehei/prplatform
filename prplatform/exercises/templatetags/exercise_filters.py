from django import template

register = template.Library()


def my_submission_count(exercise, user):
    return exercise.submissions_by_submitter(user).count()


def my_received_feedback_count(exercise, user):
    if exercise.course.is_teacher(user):
        return 0
    if exercise.reviews_available_date_in_future():
        return 0
    if not exercise.review_showing_requirements_ok(user):
        return 0
    return exercise.last_reviews_for(user).count()


def deadline_extension_for(exercise, user):
    return exercise.deadline_extension_for(user)


def max_submissions_for(exercise, user):
    return exercise.max_submissions_for(user)


register.filter('my_submission_count', my_submission_count)
register.filter('my_received_feedback_count', my_received_feedback_count)
register.filter('deadline_extension_for', deadline_extension_for)
register.filter('max_submissions_for', max_submissions_for)


