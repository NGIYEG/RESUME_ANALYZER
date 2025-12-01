from django.db import models
from Applicantapp.models import Applicant

class ResumeExtraction(models.Model):
    applicant = models.OneToOneField(Applicant, on_delete=models.CASCADE)

    extracted_text = models.TextField(null=True, blank=True)

    skills = models.JSONField(null=True, blank=True)
    work_experience = models.JSONField(null=True, blank=True)
    projects = models.JSONField(null=True, blank=True)
    education = models.JSONField(null=True, blank=True)

    processed = models.BooleanField(default=False)

    def __str__(self):
        return f"Extraction for {self.applicant.first_name}"
