from django.contrib.auth import authenticate, login
from oauthlib.oauth1 import SignatureOnlyEndpoint
from oauthlib.common import urlencode
from django_lti_login.validators import LTIRequestValidator
from django_lti_login.backends import LTIAuthBackend


def LtiLoginMiddleware(get_response):
    # One-time configuration and initialization.

    def middleware(request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.

        print("\n\n\n\nLTI_LOGIN_MIDDLEWARE --- middleware")
        print(request)


        if request.method == 'GET':
            print("THIS IS A GET")
            # for k, v in request.GET.items():
                # print(f"{k}: {v}")
            body = urlencode(request.GET.items())
        else:
            print("THIS IS A POST")
            # for k, v in request.POST.items():
                # print(f"{k}: {v}")
            body = urlencode(request.POST.items())

        uri = request.build_absolute_uri()
        method = request.method

        print(request.META.keys())
        headers = {k: v for k, v in request.META.items() if not k.startswith('wsgi.')}
        if method == 'POST':
            for k, v in request.POST.items():
                headers[k] = v

        if 'HTTP_AUTHORIZATION' in headers:
            headers['Authorization'] = headers['HTTP_AUTHORIZATION']
        if 'CONTENT_TYPE' in headers:
            headers['Content-Type'] = headers['CONTENT_TYPE']

        # uri += body
        # create oauth endpoint and validate request
        endpoint = SignatureOnlyEndpoint(LTIRequestValidator())
        print("\n\nVALIDATE STARTS:")
        print(f"URI:\n{uri}")
        uri += "&" + body
        print(f"uusI URI: \n{uri}")
        print(f"METHOD: {method}")
        print(f"BODY: \n{body}")
        headers['QUERY_STRING'] = body
        print("HEADERS:")
        for k, v in headers.items():
            print(f"{k} : {v}")
        print("\n\n")

        # urlparse + urldecode ja sitten dictin päivitys ja urlencode ja url._replace(query=new_plaaaplaa)  pitäis tuottaa sulle signaturen validoiva uusi urli



        is_valid, oauth_request = endpoint.validate_request(uri, method, '', headers)

        print(is_valid)

        if is_valid:
            print("authenticating...")

            user = LTIAuthBackend().authenticate(oauth_request=oauth_request)
            print(user)
            request.user = user

        response = get_response(request)

        # Code to be executed for each request/response after
        # the view is called.

        return response

    return middleware
