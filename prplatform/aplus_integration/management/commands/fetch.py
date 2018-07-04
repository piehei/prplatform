
from django.core.management.base import BaseCommand

from prplatform.exercises.models import SubmissionExercise
from prplatform.aplus_integration.core import get_submissions

import logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetches all submissions to all APLUS SubmissionExercises'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        exercises = SubmissionExercise.objects.filter(type=SubmissionExercise.APLUS)

        logger.info(f"Found {exercises.count()} SubmissionExercises with type APLUS")
        logger.info("Starting to fetch their details...")

        for exer in exercises:
            logger.info(f"Starting to handle {exer}")
            if get_submissions(exer):
                logger.info(f"{exer} handled")
            else:
                logger.error(f"{exer} FAILED")
