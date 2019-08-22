
from django.core.management.base import BaseCommand
from django.db import transaction

from prplatform.aplus_integration.models import AplusAPICallRequest
from prplatform.aplus_integration.core import (
        handle_submission_by_hook,
    )

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
            with transaction.atomic():
                # PLEASE NOTE:
                # this transaction *only* means rollback, the possible exception
                # is not handled here in any way which will terminate the mgmt command
                # call. since the system is configured to use sentry reporting, the
                # error will be reported there and sufficient means may be taken then.
                # if there's one tricky submission causing problems, it may be removed
                # through django admin or shell access.
                logger.debug(f"Starting to handle {call}")
                can_delete, msg = handle_submission_by_hook(call)
                if can_delete:
                    logger.debug('Hook handled the call -> deleting')
                    call.delete()

        logger.info(f"Handled all AplusAPICallRequests")
