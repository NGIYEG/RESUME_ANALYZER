from django.db import models

# Create your models here.
from django.db import models
from Companyapp.models import JobAdvertised, Application
from Extractionapp.models import ResumeExtraction

class AnalyticsReport(models.Model):
    """
    Store analytics data for job postings
    """
    job = models.ForeignKey(JobAdvertised, on_delete=models.CASCADE, related_name='analytics')
    total_applicants = models.IntegerField(default=0)
    avg_match_score = models.FloatField(default=0.0)
    top_skills_found = models.JSONField(default=list, blank=True)
    avg_experience_years = models.FloatField(default=0.0)
    education_breakdown = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-generated_at']
    
    def __str__(self):
        return f"Analytics for {self.job.post.title} - {self.generated_at}"
