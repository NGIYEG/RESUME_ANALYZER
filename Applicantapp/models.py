from django.db import models


# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class Applicant(models.Model):
    applicant_id = models.AutoField(primary_key=True)
    
   
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='applicant_profile', null=True, blank=True)
    
   
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True, help_text="e.g., Nairobi, Remote")
    
    
    linkedIn_profile = models.CharField(max_length=255, blank=True)
    portfolio_link = models.URLField(blank=True, null=True)
    
    
    resume = models.FileField(upload_to='resumes/')
    other_documents = models.FileField(upload_to='documents/', blank=True, null=True)
    
 
    converted_images = models.JSONField(blank=True, null=True)

    extracted_data = models.JSONField(blank=True, null=True)

    def __str__(self):
        if self.user:
            return self.user.username
        return f"{self.first_name} {self.last_name}"