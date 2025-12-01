from django.apps import AppConfig

class ApplicantappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Applicantapp'

    def ready(self):
        import Applicantapp.signals
