from django.urls import path
from . import views

app_name = 'Analyzerapp'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('job/<int:job_id>/', views.job_analytics, name='job_analytics'),
]
