from . import views
from django.urls import path

urlpatterns = [
    path('', views.add_department_and_post, name='add'),
    path('advertise-job/', views.create_job_advert, name='job_advert'),
     path("load-posts/", views.load_posts, name="load_posts"),
]