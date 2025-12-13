from django.shortcuts import get_object_or_404, render, redirect
from .matcher import calculate_match_percentage
from .models import Application, Department, JobAdvertised, Post, AcademicCourse
from Extractionapp.models import ResumeExtraction
from .forms import DepartmentForm, PostForm, JobAdvertisedForm, AcademicCourseForm
from django.contrib import messages
from django.http import JsonResponse

def add_department_and_post(request):
    """Handle department, post, and academic course creation"""
    dept_form = DepartmentForm()
    post_form = None
    course_form = AcademicCourseForm()

    if request.method == "POST":
        # Handle Department Creation
        if "add_department" in request.POST:
            dept_form = DepartmentForm(request.POST)
            if dept_form.is_valid():
                dept_form.save()
                messages.success(request, "✅ Department added successfully!")
                return redirect('add')
            else:
                messages.error(request, "❌ Please fix the errors in the department form.")
        
        # Handle Academic Course Creation
        if "add_course" in request.POST:
            course_form = AcademicCourseForm(request.POST)
            if course_form.is_valid():
                course = course_form.save()
                messages.success(request, f"✅ Academic course '{course.name}' added successfully!")
                return redirect('add')
            else:
                messages.error(request, "❌ Please fix the errors in the course form.")

        # Handle Post Creation
        if "add_post" in request.POST:
            post_form = PostForm(request.POST)
            if post_form.is_valid():
                post = post_form.save(commit=False)
                post.save()
                
                # Save the many-to-many relationship
                post_form.save_m2m()
                
                courses_count = post.required_courses.count()
                messages.success(
                    request, 
                    f"✅ Post '{post.title}' added with {courses_count} required course(s)!"
                )
                return redirect('add')
            else:
                messages.error(request, "❌ Please fix the errors in the post form.")

    # Initialize forms for GET request
    if Department.objects.exists():
        post_form = PostForm()
    
    # Get existing courses for display
    existing_courses = AcademicCourse.objects.all().order_by('name')
    
    # Get existing posts with their courses for display
    existing_posts = Post.objects.all().prefetch_related('required_courses', 'department')

    context = {
        'dept_form': dept_form,
        'post_form': post_form,
        'course_form': course_form,
        'existing_courses': existing_courses,
        'existing_posts': existing_posts,
    }
    return render(request, "add_dept_post.html", context)


def create_job_advert(request):
    """Create job advertisement with course selection"""
    if request.method == "POST":
        form = JobAdvertisedForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.save()
            
            # Save the many-to-many relationship for courses
            form.save_m2m()
            
            courses_count = job.selected_courses.count()
            messages.success(
                request, 
                f"✅ Job advertisement created successfully with {courses_count} accepted course(s)!"
            )
            return redirect("job_advert")
        else:
            messages.error(request, "❌ Please fix the errors below.")
    else:
        form = JobAdvertisedForm()

    return render(request, "advertise_job.html", {"form": form})


def load_posts(request):
    """AJAX endpoint to load posts for a department"""
    department_id = request.GET.get("department")
    posts = Post.objects.filter(department_id=department_id).values("id", "title")
    return JsonResponse(list(posts), safe=False)


def load_courses(request):
    """AJAX endpoint to load courses for a selected post"""
    post_id = request.GET.get("post")
    
    try:
        post = Post.objects.get(id=post_id)
        courses = post.required_courses.all().values("id", "name", "code")
        
        return JsonResponse({
            'success': True,
            'courses': list(courses)
        })
    except Post.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Post not found'
        }, status=404)


def job_applicants_ranked(request, job_id):
    """
    Display ranked applicants for a specific job based on matching algorithm.
    Now includes academic course matching.
    """
    job = get_object_or_404(JobAdvertised, id=job_id)
    
    # Get job's accepted courses
    job_courses = job.get_selected_courses_list()
    
    applications = Application.objects.filter(post=job.post).select_related('applicant')
    
    ranked_candidates = []

    for app in applications:
        # Fetch resume extraction data
        try:
            extraction = ResumeExtraction.objects.get(applicant=app.applicant)
            
            resume_data = {
                'skills': extraction.skills or [],
                'work_experience': extraction.work_experience or [],
                'education': extraction.education or [],
                'projects': extraction.projects or []
            }
            
            processing_status = "Processed" if extraction.processed else "Pending"
            
        except ResumeExtraction.DoesNotExist:
            resume_data = {
                'skills': [],
                'work_experience': [],
                'education': [],
                'projects': []
            }
            processing_status = "Not Started"

        # Calculate match score with academic course consideration
        match_result = calculate_match_percentage(
            job, 
            resume_data, 
            linkedin_data={},
            job_courses=job_courses  # Pass job courses
        )
        
        ranked_candidates.append({
            'applicant': app.applicant,
            'score': match_result['total_score'],
            'skills_score': match_result['skills_score'],
            'experience_score': match_result['experience_score'],
            'education_score': match_result['education_score'],
            'course_match_score': match_result.get('course_match_score', 0),
            'matched_skills': match_result['matched_skills'],
            'missing_skills': match_result['missing_skills'],
            'matched_courses': match_result.get('matched_courses', []),
            'resume_skills': resume_data.get('skills', []),
            'resume_experience': resume_data.get('work_experience', []),
            'resume_education': resume_data.get('education', []),
            'candidate_years': match_result['candidate_years'],
            'required_years': match_result['required_years'],
            'application_date': app.applied_at,
            'status': processing_status
        })

    # Sort by highest score first
    ranked_candidates.sort(key=lambda x: x['score'], reverse=True)

    context = {
        'job': job,
        'candidates': ranked_candidates,
        'job_courses': job_courses
    }
    return render(request, 'ranked_applicants.html', context)

def manage_jobs(request):
    jobs = JobAdvertised.objects.select_related('post', 'department').all().order_by('-created_at')
    
    job_data = []
    for job in jobs:
        # FIX: Use 'job.post' because Application is linked to the Post model, not JobAdvertised
        count = Application.objects.filter(post=job.post).count()
        
        job_data.append({
            'job': job,
            'applicant_count': count,
            'selected_courses': job.selected_courses.all()
        })
    
    return render(request, 'job_list.html', {'job_data': job_data})

def edit_job(request, job_id):
    """
    Allows editing an existing job advertisement.
    """
    job = get_object_or_404(JobAdvertised, id=job_id)
    
    if request.method == 'POST':
        form = JobAdvertisedForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            messages.success(request, f"Job '{job.post.title}' updated successfully!")
            return redirect('manage_jobs')
    else:
        form = JobAdvertisedForm(instance=job)
        
    return render(request, 'advertise_job.html', {
        'form': form,
        'is_edit': True, # Flag to change button text in template
        'job': job
    })


def delete_job(request, job_id):
    """
    Deletes a job advertisement.
    """
    job = get_object_or_404(JobAdvertised, id=job_id)
    
    if request.method == 'POST':
        title = job.post.title
        job.delete()
        messages.success(request, f"Job '{title}' has been deleted.")
        return redirect('manage_jobs')
    
    # Render a simple confirmation page
    return render(request, 'delete_confirm.html', {'job': job})