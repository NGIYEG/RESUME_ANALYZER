from django.shortcuts import render
from django.shortcuts import render, redirect
from .forms import DepartmentForm, PostForm, JobAdvertisedForm
from .models import Department, Post
from django.contrib import messages
from django.http import JsonResponse
 
# Create your views here.

def add_department_and_post(request):
    dept_form = DepartmentForm()
    post_form = None   # Post form hidden at first

    if request.method == "POST":
        if "add_department" in request.POST:
            dept_form = DepartmentForm(request.POST)
            if dept_form.is_valid():
                dept_form.save()
                return redirect('add')

        if "add_post" in request.POST:
            post_form = PostForm(request.POST)
            if post_form.is_valid():
                post_form.save()
                return redirect('add')

    # Only show post form if there is at least one department
    if Department.objects.exists():
        post_form = PostForm()

    context = {
        'dept_form': dept_form,
        'post_form': post_form,
    }
    return render(request, "add_dept_post.html", context)
   

def create_job_advert(request):
    if request.method == "POST":
        form = JobAdvertisedForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Job advertisement created successfully!")
            return redirect("job_advert")  # change to your desired URL name
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = JobAdvertisedForm()

    return render(request, "advertise_job.html", {"form": form})




def load_posts(request):
    department_id = request.GET.get("department")
    posts = Post.objects.filter(department_id=department_id).values("id", "title")
    return JsonResponse(list(posts), safe=False)
