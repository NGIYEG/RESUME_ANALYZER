from django.contrib import admin
from .models import JobAdvertised, Post, Application, Department
# Register your models here.
admin.site.register(Post)
admin.site.register(Application)
admin.site.register(Department)
admin.site.register(JobAdvertised)