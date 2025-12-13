# views.py
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import get_object_or_404, redirect, render
from .forms import ApplicantApplyForm, ApplicantProfileForm, UserRegisterForm
from .models import Applicant
from .tasks import process_resume_task
from Companyapp.matcher import calculate_match_percentage
from Companyapp.models import Application, JobAdvertised
from Extractionapp.models import ResumeExtraction

def register_view(request):
    if request.method == 'POST':
        user_form = UserRegisterForm(request.POST)
        profile_form = ApplicantProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.set_password(user_form.cleaned_data['password'])
            user.save()
            
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            # Trigger Extraction immediately for the Smart Feed
            process_resume_task.delay(profile.id)
            
            login(request, user)
            messages.success(request, "Account created! We are analyzing your resume...")
            return redirect('job_feed')
    else:
        user_form = UserRegisterForm()
        profile_form = ApplicantProfileForm()
        
    return render(request, 'register.html', {'user_form': user_form, 'profile_form': profile_form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('job_feed')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')



def job_feed(request):
    jobs = JobAdvertised.objects.all()
    
    # If user is logged in and has a processed resume, sort by match
    if request.user.is_authenticated:
        try:
            profile = request.user.applicant_profile
            
            # Only run matching if we have extracted data
            if profile.extracted_data:
                ranked_jobs = []
                
                for job in jobs:
                    # Run the Matcher
                    score_data = calculate_match_percentage(job, profile.extracted_data)
                    score = score_data['total_score']
                    
                    # Boost score if locations match (Simple check)
                    # Assuming JobAdvertised has a 'location' field or we check text
                    if profile.location and profile.location.lower() in job.description.lower():
                        score += 5 # 5% Bonus for location match
                    
                    # Attach score to job object temporarily for the template
                    job.match_score = int(round(score))
                    ranked_jobs.append(job)
                
                # Sort: Highest score first
                ranked_jobs.sort(key=lambda x: x.match_score, reverse=True)
                jobs = ranked_jobs
                
        except Applicant.DoesNotExist:
            pass # User is admin or has no profile, show default list

    return render(request, 'job_feed.html', {'jobs': jobs})


def apply_for_job(request):
    # 1. Get job_id from the URL query string (e.g., ?job_id=5)
    job_id = request.GET.get('job_id') 
    
    selected_job = None
    initial_data = {}

    # 2. If ID exists, fetch the job
    if job_id:
        selected_job = get_object_or_404(JobAdvertised, id=job_id)
        initial_data = {'job': selected_job}

    if request.method == "POST":
        form = ApplicantApplyForm(request.POST, request.FILES)
        if form.is_valid():
            applicant = form.save()
            job_advert = form.cleaned_data['job']
            Application.objects.create(applicant=applicant, post=job_advert.post)
            
            # Trigger Celery Task
            process_resume_task.delay(applicant.applicant_id)

            messages.success(request, "Application received! Processing in background.")
            return redirect("job_feed")
    else:
        form = ApplicantApplyForm(initial=initial_data)

    jobs = JobAdvertised.objects.all()

    return render(request, "job_application.html", {
        "form": form, 
        "jobs": jobs,
        "selected_job": selected_job
    })

    
from Extractionapp.models import ResumeExtraction

def view_resume_insights(request, applicant_id):
    # Get the extraction object or return 404 if not ready yet
    extraction = get_object_or_404(ResumeExtraction, applicant_id=applicant_id)
    
    context = {
        "applicant": extraction.applicant,
        "raw_text": extraction.extracted_text,
        "skills": extraction.skills,
        "experience": extraction.work_experience,
        "projects": extraction.projects,
        "education": extraction.education,
    }
    return render(request, "resume_insights.html", context)