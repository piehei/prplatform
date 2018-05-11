from django.apps import AppConfig


class SubmissionsConfig(AppConfig):
    name = "prplatform.submissions"
    verbose_name = "Submissions"

    def ready(self):
        """Override this to put in:
            Courses system checks
            Courses signal registration
        """
        try:
            import submissions.signals  # noqa F401
        except ImportError:
            pass

