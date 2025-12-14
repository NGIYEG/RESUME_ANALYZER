from . import views
from django.urls import path

app_name = 'career'

urlpatterns = [
    # path('', views.index, name='index')
    path('', views.login_view, name='login'),
     path('feed/', views.job_feed, name='job_feed'),
     path('apply/', views.apply_for_job, name='apply_job'),
     path('insights/<int:applicant_id>/', views.view_resume_insights, name='resume_insights'),
     path('register/', views.register_view, name='register'),
     path('logout/', views.logout_view, name='logout'),
     path('profile/', views.profile_view, name='profile_dashboard'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/view/<int:pk>/', views.public_profile_view, name='public_profile'),
]