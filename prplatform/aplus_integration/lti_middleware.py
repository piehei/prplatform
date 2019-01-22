from django.db import IntegrityError
from django.contrib.auth import authenticate, login
from django.urls import resolve
from oauthlib.oauth1 import SignatureOnlyEndpoint
from oauthlib.common import urlencode
from urllib.parse import urlparse
from django_lti_login.validators import LTIRequestValidator
from django_lti_login.backends import LTIAuthBackend
from django.utils.deprecation import MiddlewareMixin

from prplatform.courses.models import Course
from prplatform.users.models import User


class LtiLoginMiddleware(MiddlewareMixin):

    def __init__(self, get_response=None):
        # One-time configuration and initialization.
        self.get_response = get_response

    def __call__(self, request):

        request.LTI_MODE = False

        uri = urlparse(request.build_absolute_uri())
        method = request.method

        query_dict = {}
        if request.POST:
            query_dict.update(request.POST.items())
        if request.GET:
            query_dict.update(request.GET.items())

        if 'lti_message_type' in query_dict and \
           'lti_version' in query_dict and \
           'oauth_consumer_key' in query_dict:

            uri = uri._replace(query=urlencode(query_dict.items())).geturl()

            headers = {k: v for k, v in request.META.items() if not k.startswith('wsgi.')}

            if 'HTTP_AUTHORIZATION' in headers:
                headers['Authorization'] = headers['HTTP_AUTHORIZATION']
            if 'CONTENT_TYPE' in headers:
                headers['Content-Type'] = headers['CONTENT_TYPE']

            endpoint = SignatureOnlyEndpoint(LTIRequestValidator())

            is_valid, oauth_request = endpoint.validate_request(uri, method, '', headers)

            if is_valid:

                # if the same person has accessed the system via LTI/shibboleth previously
                # then there already exists a user account for him/her
                # in that case, login that user account, otherwise create a new one

                try:
                    user = User.objects.get(email=oauth_request.lis_person_contact_email_primary)
                    print("previous user found! login")
                except Exception:
                    print("previous user NOT FOUND --> create a new one")
                    user = LTIAuthBackend().authenticate(oauth_request=oauth_request)

                resolved_view = resolve(request.path)
                course = Course.objects.get(
                        base_course__url_slug=resolved_view.kwargs['base_url_slug'],
                        url_slug=resolved_view.kwargs['url_slug'])

                course.enroll(user)
                request.user = user

                # since the HTTP POSTs are coming through a proxy(ish) server that drops
                # cookies but keeps CSRF tokens, the CSRF check always fails
                # in this case we can disable the checks alltogether
                setattr(request, '_dont_enforce_csrf_checks', True)

                # this tells the view classes they should provide the LTI version of the page
                request.LTI_MODE = True

        response = self.get_response(request)

        return response
