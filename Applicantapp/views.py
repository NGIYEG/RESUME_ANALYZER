
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
            return redirect('career:job_feed')
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
            return redirect('career:job_feed')
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('career:login')

# Applicantapp/views.py

@login_required
def profile_view(request):
    """The main dashboard/profile page for the logged-in user"""
    user = request.user
    
    # 1. Try to get the profile linked to this user
    try:
        applicant = user.applicant_profile
    except Applicant.DoesNotExist:
        # 2. If not linked, check if a profile exists with the same email (orphaned)
        if Applicant.objects.filter(email=user.email).exists():
            applicant = Applicant.objects.get(email=user.email)
            # Link it to the current user so this doesn't happen again
            applicant.user = user
            applicant.save()
        else:
            # 3. If strictly no profile exists, create a new one safely
            applicant = Applicant.objects.create(
                user=user, 
                email=user.email,
                first_name=user.first_name, 
                last_name=user.last_name
            )

    # Render the dashboard template you provided
    return render(request, 'profile_dashboard.html', {'profile': applicant})

@login_required
def profile_edit(request):
    """Handles profile editing"""
    try:
        applicant = request.user.applicant_profile
    except Applicant.DoesNotExist:
        applicant = Applicant.objects.create(user=request.user)

    if request.method == 'POST':
        # Pass user object to the form
        form = ApplicantProfileForm(request.POST, request.FILES, instance=applicant, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            # Redirect to the dashboard after edit
            return redirect('career:profile_dashboard') 
    else:
        form = ApplicantProfileForm(instance=applicant, user=request.user)

    return render(request, 'profile_edit.html', {'form': form})

def job_feed(request):
    # 1. Start with all jobs
    jobs = JobAdvertised.objects.all()
    
    # If user is logged in, filter out applied jobs and run matching
    if request.user.is_authenticated:
        try:
            profile = request.user.applicant_profile
            
       
            applied_job_ids = Application.objects.filter(applicant=profile).values_list('post_id', flat=True)
            
       
            jobs = jobs.exclude(id__in=applied_job_ids)
     
            if profile.extracted_data:
                ranked_jobs = []
                
                for job in jobs:
                    # Run the Matcher
                    score_data = calculate_match_percentage(job, profile.extracted_data)
                    score = score_data['total_score']
                    
                    # Boost score if locations match
                    if profile.location and job.description and profile.location.lower() in job.description.lower():
                        score += 5 
                    
                    # Attach score to job object temporarily
                    job.match_score = int(round(score))
                    ranked_jobs.append(job)
                
                # Sort: Highest score first
                ranked_jobs.sort(key=lambda x: x.match_score, reverse=True)
                jobs = ranked_jobs
                
        except Applicant.DoesNotExist:
            pass # User is admin or company, show default list

    return render(request, 'job_feed.html', {'jobs': jobs})



@login_required
def apply_for_job(request):
    # 1. Get job_id from the URL query string (e.g., ?job_id=5)
    job_id = request.GET.get('job_id') 
    
    if job_id and request.user.is_authenticated:
        try:
            # Get the profile
            applicant_profile = request.user.applicant_profile
            # Get the job being accessed
            target_job = get_object_or_404(JobAdvertised, id=job_id)
            
            # Check database for existing application
            if Application.objects.filter(applicant=applicant_profile, post=target_job.post).exists():
                messages.warning(request, "You have already applied for this position.")
                return redirect("job_feed")
        except Exception:
           
            pass
  

    selected_job = None
    initial_data = {}

  
    if job_id:
        selected_job = get_object_or_404(JobAdvertised, id=job_id)
        initial_data = {'job': selected_job}

    if request.method == "POST":
        form = ApplicantApplyForm(request.POST, request.FILES)
        if form.is_valid():
            # Get the job from the form data
            job_advert = form.cleaned_data['job']
            
          
            if hasattr(request.user, 'applicant_profile'):
                applicant = request.user.applicant_profile
            else:
                # Fallback: create/save if it's a new profile logic
                applicant = form.save()


            if Application.objects.filter(applicant=applicant, post=job_advert.post).exists():
                messages.warning(request, "You have already applied for this position.")
                return redirect("job_feed")
            # ============================================================

            # Save the new Application
            Application.objects.create(applicant=applicant, post=job_advert.post)
            
            # Trigger Celery Task
            process_resume_task.delay(applicant.applicant_id)

            messages.success(request, "Application received! Processing in background.")
            return redirect("career:job_feed")
    else:
        form = ApplicantApplyForm(initial=initial_data)

    # Filter out jobs user has already applied for in the sidebar list too (Optional but good UX)
    jobs = JobAdvertised.objects.all()
    if hasattr(request.user, 'applicant_profile'):
        applied_ids = Application.objects.filter(applicant=request.user.applicant_profile).values_list('post_id', flat=True)
        jobs = jobs.exclude(id__in=applied_ids)

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



def public_profile_view(request, pk):
    # 1. Fetch the specific applicant by ID
    applicant = get_object_or_404(Applicant, pk=pk)
    
    # 2. Get their user object
    user = applicant.user
    
    # 3. Render the dashboard, but pass the specific 'profile' and 'user'
    return render(request, 'public_profile.html', {
        'profile': applicant,
        'user': user
    })