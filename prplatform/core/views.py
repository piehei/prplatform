from django.conf import settings
from django.shortcuts import render


def handler_500(request):
    return render(request,
            '500.html',
            { 'contact_email': settings.ADMIN_CONTACT_EMAIL })
