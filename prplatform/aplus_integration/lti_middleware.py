from django.contrib.auth import authenticate, login
from django.urls import resolve
from oauthlib.oauth1 import SignatureOnlyEndpoint
from oauthlib.common import urlencode
from urllib.parse import urlparse
from django_lti_login.validators import LTIRequestValidator
from django_lti_login.backends import LTIAuthBackend

from prplatform.courses.models import Course


def LtiLoginMiddleware(get_response):

    def middleware(request):

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
                user = LTIAuthBackend().authenticate(oauth_request=oauth_request)

                resolved_view = resolve(request.path)
                course = Course.objects.get(
                        base_course__url_slug=resolved_view.kwargs['base_url_slug'],
                        url_slug=resolved_view.kwargs['url_slug'])

                course.enroll(user)
                request.user = user

        response = get_response(request)

        return response

    return middleware
