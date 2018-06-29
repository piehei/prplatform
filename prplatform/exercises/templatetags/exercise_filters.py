from django import template

register = template.Library()


def my_submission_count(exercise, user):
    return exercise.submissions.filter(submitter=user).count()

register.filter('my_submission_count', my_submission_count)
