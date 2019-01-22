from django.apps import AppConfig


class AplusIntegrationConfig(AppConfig):
    name = "prplatform.aplus_integration"
    verbose_name = "Aplus Integration module"

    def ready(self):
        """Override this to put in:
            Courses system checks
            Courses signal registration
        """
        pass
