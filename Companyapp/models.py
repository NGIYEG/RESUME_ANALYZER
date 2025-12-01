from django.db import models
from django.utils import timezone
from Applicantapp.models import Applicant
from django.utils.text import slugify

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Post(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name="posts"
    )
    title = models.CharField(max_length=100)
    
  

    applicants = models.ManyToManyField(
        Applicant,
        through='Application',
        related_name='applied_posts'
    )

    def __str__(self):
        return self.title


class Application(models.Model):
    applicant = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    post = models.ForeignKey('Post', on_delete=models.CASCADE)  # FIXED HERE
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('Pending','Pending'), ('Accepted','Accepted'), ('Rejected','Rejected')],
        default='Pending'
    )

    class Meta:
        unique_together = ('applicant', 'post')

    def __str__(self):
        return f"{self.applicant} → {self.post}"

class JobAdvertised(models.Model):
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='job_adverts'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='job_adverts'
    )
    description = models.TextField()
    keywords = models.CharField(max_length=255, blank=True)  # requirements
    deadline = models.DateTimeField()
    max_applicants = models.PositiveIntegerField(default=1)  # <-- ADD THIS
    created_at = models.DateTimeField(auto_now_add=True)
    

    def is_open(self):
        return timezone.now() < self.deadline

    def __str__(self):
        return f"{self.post.title} in {self.department.name}"

    class Meta:
        ordering = ['-created_at']
