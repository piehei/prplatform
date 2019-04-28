# XXX: for django-lti-login
"""
Example receiver hooks to use oauth data provided by django-lti-login.
Remember to use this kind of functions to store what ever data you need from oauth.

In addition, don't forget to load this file (so the hooks are connected).
See how `apps.py` includes this file when django apps are loaded.
"""
import logging
from django.urls import resolve
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import PermissionDenied
from django.dispatch import receiver
from django_lti_login.signals import lti_login_authenticated

from prplatform.courses.models import Course, Enrollment
from prplatform.courses.utils import get_email_candidates
from prplatform.users.models import User

logger = logging.getLogger('users.receivers')


@receiver(user_logged_in)
def change_original_submission_submitters(sender, **kwargs):
    """
        when reviewexervise of type GROUP where stundents review each other is used,
        it might happen that someone has never logged in before another user wants
        to create a review for that particular user. in that case, a temporary
        user account it automatically created. if we can find a temp user for
        newly logged in user, move all submissions in that user's name
        to this logged in user and destroy the temp user.
    """

    request = kwargs.get('request', None)
    user = kwargs.get('user', None)

    # user's email + any valid email domains defined in local_settings.py
    candidates = get_email_candidates(user)
    temp_user = User.objects.filter(email__in=candidates, temporary=True).first()

    if request and user and temp_user:

        enrolled_courses = []

        logger.info(f"Changing the submitter of original submissions for")
        for sub in temp_user.originalsubmission_submitters.all():
            logger.info(sub)
            sub.submitter_user = user
            sub.save()

            if sub.course not in enrolled_courses:
                Enrollment.objects.create(course=sub.course, student=user)
                logger.info(f"enrolled to {sub.course}")

        # TODO: if this implementation holds, check there's no concurrency bugs
        logger.info(f"Original submissions by {temp_user}({temp_user.username}/{temp_user.email}) have been modified to be "
                    f"submitted by {user}({user.username}/{user.email}")
        logger.info(f"Deleting temp_user {temp_user}")

        ret = temp_user.delete()
        logger.info(ret)
    else:
        logger.info(f"No temp_user existed for {user}")


@receiver(lti_login_authenticated)
def store_last_login(sender, **kwargs):
    """
    Example thing to do before user is actually authenticated, but does exists.
    Django sets user.last_login after this, so it's last time to use it.
    """
    request = kwargs.get('request', None)
    user = kwargs.get('user', None)
    if request and user:
        request.session['last_login'] = str(user.last_login)


@receiver(user_logged_in)
def store_course_info(sender, **kwargs):
    """
    Example things to do after user is fully authenticated.
    You can still raise PermissionDenied here.
    """

    request = kwargs.get('request', None)
    session = request.session
    user = kwargs.get('user', None)
    oauth = getattr(request, 'oauth', None)
    if request and user and oauth:
        course_lms = getattr(oauth, 'tool_consumer_instance_name', None)  # Example LMS
        course_id = getattr(oauth, 'context_id', None)  # lms.example.com/it-101/
        course_label = getattr(oauth, 'context_label', None)  # IT-101
        course_name = getattr(oauth, 'context_title', None)  # Basics on IT

        if course_id is None or course_label is None or course_name is None:
            # Invalid lti login due to missing information
            logger.error("LTI login request doesn't contain all required "
                         "fields (context_id, context_label, context_title) "
                         "for course membership update."
                         "User that tried to login: {}".format(user))
            raise PermissionDenied("Not all required fields present in LTI login")

        logger.info("New authentication by {user} for {label} {name}.".format(
            user=user,
            label=course_label,
            name=course_name,
        ))

        session['course_id'] = course_id
        session['course_label'] = course_label
        session['course_name'] = course_name
        session['course_lms'] = course_lms

        # the consumer side of LTI has appended assignment_url to GET params
        # --> something like ?assignment_url=/courses/prog1/F2018/exercises/r/1
        destination_url = request.GET.get('assignment_url', '/courses/')
        url_kwargs = resolve(destination_url).kwargs

        course = Course.objects.get(base_course__url_slug=url_kwargs['base_url_slug'],
                                    url_slug=url_kwargs['url_slug'])

        if not course.is_enrolled(user):
            course.enroll(user)
        oauth.redirect_url = destination_url

        # List LTI params in debug
        if settings.DEBUG:
            logger.debug("LTI login accepted for user %s", user)
            for k, v in sorted(oauth.params):
                logger.debug("  \w param -- %s: %s", k, v)
