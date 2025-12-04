from django.shortcuts import get_object_or_404, render, redirect
from .matcher import calculate_match_percentage
from .models import Application, Department, JobAdvertised, Post
from Extractionapp.models import ResumeExtraction
from .forms import DepartmentForm, PostForm, JobAdvertisedForm
from django.contrib import messages
from django.http import JsonResponse

def add_department_and_post(request):
    dept_form = DepartmentForm()
    post_form = None

    if request.method == "POST":
        if "add_department" in request.POST:
            dept_form = DepartmentForm(request.POST)
            if dept_form.is_valid():
                dept_form.save()
                messages.success(request, "Department added successfully!")
                return redirect('add')

        if "add_post" in request.POST:
            post_form = PostForm(request.POST)
            if post_form.is_valid():
                post_form.save()
                messages.success(request, "Post added successfully!")
                return redirect('add')

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
            return redirect("job_advert")
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = JobAdvertisedForm()

    return render(request, "advertise_job.html", {"form": form})

def load_posts(request):
    department_id = request.GET.get("department")
    posts = Post.objects.filter(department_id=department_id).values("id", "title")
    return JsonResponse(list(posts), safe=False)

def job_applicants_ranked(request, job_id):
    """
    Display ranked applicants for a specific job based on matching algorithm.
    """
    job = get_object_or_404(JobAdvertised, id=job_id)
    
    # FIXED: Use 'post' instead of 'job'
    applications = Application.objects.filter(post=job.post).select_related('applicant')
    
    ranked_candidates = []

    for app in applications:
        # Fetch resume extraction data
        try:
            extraction = ResumeExtraction.objects.get(applicant=app.applicant)
            
            # FIXED: Build resume_data from model fields, not 'extracted_data'
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

        # Calculate match score (now returns detailed breakdown)
        match_result = calculate_match_percentage(job, resume_data, linkedin_data={})
        
        ranked_candidates.append({
            'applicant': app.applicant,
            'score': match_result['total_score'],
            'skills_score': match_result['skills_score'],
            'experience_score': match_result['experience_score'],
            'education_score': match_result['education_score'],
            'matched_skills': match_result['matched_skills'],
            'missing_skills': match_result['missing_skills'],
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
        'candidates': ranked_candidates
    }
    return render(request, 'ranked_applicants.html', context)