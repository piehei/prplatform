
from django.core.management.base import BaseCommand

from prplatform.exercises.models import SubmissionExercise

from prplatform.aplus_integration.models import AplusAPICallRequest
from prplatform.aplus_integration.core import (
        handle_submission_by_hook,
    )

import requests

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetches all submissions to all APLUS SubmissionExercises'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        pending_calls = AplusAPICallRequest.objects.all()

        logger.info(f"Found {pending_calls.count()} AplusAPICallRequests ---> fetch now")

        for call in pending_calls:
            can_delete, msg = handle_submission_by_hook(call)
            if can_delete:
                logger.info('hook request handled -> deleting')
                call.delete()


