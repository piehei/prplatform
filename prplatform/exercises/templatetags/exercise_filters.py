from django import template

register = template.Library()


def my_submission_count(exercise, user):

    if exercise.use_groups:
        return exercise.submissions.filter(submitter_group=exercise.course.find_studentgroup_by_user(user)).count()

    return exercise.submissions.filter(submitter_user=user).count()

register.filter('my_submission_count', my_submission_count)
