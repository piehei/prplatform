from django.apps import AppConfig


class ExercisesConfig(AppConfig):
    name = "prplatform.exercises"
    verbose_name = "Exercises"

    def ready(self):
        """Override this to put in:
            Courses system checks
            Courses signal registration
        """
        try:
            import exercises.signals  # noqa F401
        except ImportError:
            pass

