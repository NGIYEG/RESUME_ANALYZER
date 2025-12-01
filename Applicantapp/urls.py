from . import views
from django.urls import path

urlpatterns = [
    # path('', views.index, name='index'),
    path("apply-job/", views.apply_for_job, name="apply_job"),

]