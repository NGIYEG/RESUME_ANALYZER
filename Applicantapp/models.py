from django.db import models


# Create your models here.
class Applicant(models.Model):
    applicant_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    resume = models.FileField(upload_to='resumes/')
    other_documents = models.FileField(upload_to='documents/', blank=True, null=True)
    linkedIn_profile = models.CharField(max_length=255, blank=True)
    portfolio_link = models.URLField(blank=True, null=True)
    converted_images = models.JSONField(blank=True, null=True)


    def __str__(self):
        return f"{self.first_name} {self.last_name}"
