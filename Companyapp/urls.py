from . import views
from django.urls import path

urlpatterns = [
    path('', views.add_department_and_post, name='add'),
    path('advertise-job/', views.create_job_advert, name='job_advert'),
    path("load-posts/", views.load_posts, name="load_posts"),
    path("load-courses/", views.load_courses, name="load_courses"),  # NEW
    path('job/<int:job_id>/applicants/', views.job_applicants_ranked, name='rankings'),
    path('manage-jobs/', views.manage_jobs, name='manage_jobs'),  # The Admin Dashboard
    path('edit-job/<int:job_id>/', views.edit_job, name='edit_job'), # Edit Logic
    path('delete-job/<int:job_id>/', views.delete_job, name='delete_job'), # Delete Logic
]