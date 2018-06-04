# XXX: for django-lti-login
"""
Example receiver hooks to use oauth data provided by django-lti-login.
Remember to use this kind of functions to store what ever data you need from oauth.

In addition, don't forget to load this file (so the hooks are connected).
See how `apps.py` includes this file when django apps are loaded.
"""
import logging
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core.exceptions import PermissionDenied
from django.dispatch import receiver
from django_lti_login.signals import lti_login_authenticated


logger = logging.getLogger('users.receivers')


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
        course_lms = getattr(oauth, 'tool_consumer_instance_name', None) # Example LMS
        course_id = getattr(oauth, 'context_id', None) # lms.example.com/it-101/
        course_label = getattr(oauth, 'context_label', None) # IT-101
        course_name = getattr(oauth, 'context_title', None) # Basics on IT

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

        # redirect to assignment_url from GET params
        oauth.redirect_url = request.GET.get('assignment_url', '/courses/')

        # List LTI params in debug
        if settings.DEBUG:
            logger.debug("LTI login accepted for user %s", user)
            for k, v in sorted(oauth.params):
                logger.debug("  \w param -- %s: %s", k, v)
