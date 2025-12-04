


from django.contrib import admin
from .models import AnalyticsReport

# Register your models here.
@admin.register(AnalyticsReport)
class AnalyticsReportAdmin(admin.ModelAdmin):
    list_display = ['job', 'total_applicants', 'avg_match_score', 'generated_at']
    list_filter = ['generated_at', 'job__department']
    search_fields = ['job__post__title']
    readonly_fields = ['generated_at']