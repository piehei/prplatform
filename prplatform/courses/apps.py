from django.apps import AppConfig


class CoursesConfig(AppConfig):
    name = "prplatform.courses"
    verbose_name = "Courses"

    def ready(self):
        """Override this to put in:
            Courses system checks
            Courses signal registration
        """
        try:
            import courses.signals  # noqa F401
        except ImportError:
            pass

