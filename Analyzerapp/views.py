from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, get_object_or_404
from django.db.models import Avg, Count
from Companyapp.models import JobAdvertised, Application
from Extractionapp.models import ResumeExtraction
from Companyapp.matcher import calculate_match_percentage
from collections import Counter

def dashboard(request):
    """
    Main analytics dashboard showing overview of all jobs
    """
    jobs = JobAdvertised.objects.all()
    
    dashboard_data = []
    for job in jobs:
        applications = Application.objects.filter(post=job.post)
        
        total_apps = applications.count()
        processed = 0
        total_score = 0
        all_skills = []
        
        for app in applications:
            try:
                extraction = ResumeExtraction.objects.get(applicant=app.applicant)
                if extraction.processed:
                    processed += 1
                    
                    resume_data = {
                        'skills': extraction.skills or [],
                        'work_experience': extraction.work_experience or [],
                        'education': extraction.education or [],
                    }
                    
                    result = calculate_match_percentage(job, resume_data)
                    total_score += result['total_score']
                    all_skills.extend(extraction.skills or [])
            except ResumeExtraction.DoesNotExist:
                continue
        
        avg_score = (total_score / processed) if processed > 0 else 0
        top_skills = [skill for skill, count in Counter(all_skills).most_common(5)]
        
        dashboard_data.append({
            'job': job,
            'total_applicants': total_apps,
            'processed': processed,
            'avg_match_score': round(avg_score, 1),
            'top_skills': top_skills,
            'is_open': job.is_open()
        })
    
    context = {
        'dashboard_data': dashboard_data,
        'total_jobs': jobs.count(),
        'total_applications': Application.objects.count(),
    }
    
    return render(request, 'dashboard.html', context)


def job_analytics(request, job_id):
    """
    Detailed analytics for a specific job
    """
    job = get_object_or_404(JobAdvertised, id=job_id)
    applications = Application.objects.filter(post=job.post).select_related('applicant')
    
    # Collect detailed statistics
    stats = {
        'total_applicants': applications.count(),
        'processed': 0,
        'pending': 0,
        'scores': [],
        'skills_breakdown': Counter(),
        'experience_years': [],
        'education_levels': Counter(),
    }
    
    applicants_data = []
    
    for app in applications:
        try:
            extraction = ResumeExtraction.objects.get(applicant=app.applicant)
            
            if extraction.processed:
                stats['processed'] += 1
                
                resume_data = {
                    'skills': extraction.skills or [],
                    'work_experience': extraction.work_experience or [],
                    'education': extraction.education or [],
                }
                
                result = calculate_match_percentage(job, resume_data)
                stats['scores'].append(result['total_score'])
                
                # Skills breakdown
                for skill in (extraction.skills or []):
                    stats['skills_breakdown'][skill.lower()] += 1
                
                # Experience breakdown
                stats['experience_years'].append(result['candidate_years'])
                
                # Education breakdown
                for edu in (extraction.education or []):
                    if 'phd' in edu.lower():
                        stats['education_levels']['PhD'] += 1
                    elif 'master' in edu.lower():
                        stats['education_levels']['Master'] += 1
                    elif 'bachelor' in edu.lower():
                        stats['education_levels']['Bachelor'] += 1
                    elif 'diploma' in edu.lower():
                        stats['education_levels']['Diploma'] += 1
                
                applicants_data.append({
                    'name': f"{app.applicant.first_name} {app.applicant.last_name}",
                    'email': app.applicant.email,
                    'score': result['total_score'],
                    'applied_date': app.applied_at,
                })
            else:
                stats['pending'] += 1
                
        except ResumeExtraction.DoesNotExist:
            stats['pending'] += 1
    
    # Calculate averages
    avg_score = sum(stats['scores']) / len(stats['scores']) if stats['scores'] else 0
    avg_experience = sum(stats['experience_years']) / len(stats['experience_years']) if stats['experience_years'] else 0
    
    # Top skills
    top_skills = [
        {'skill': skill, 'count': count}
        for skill, count in stats['skills_breakdown'].most_common(10)
    ]
    
    # Score distribution
    score_ranges = {
        '80-100': len([s for s in stats['scores'] if s >= 80]),
        '60-79': len([s for s in stats['scores'] if 60 <= s < 80]),
        '40-59': len([s for s in stats['scores'] if 40 <= s < 60]),
        '0-39': len([s for s in stats['scores'] if s < 40]),
    }
    
    context = {
        'job': job,
        'stats': stats,
        'avg_score': round(avg_score, 1),
        'avg_experience': round(avg_experience, 1),
        'top_skills': top_skills,
        'score_ranges': score_ranges,
        'education_breakdown': dict(stats['education_levels']),
        'applicants': sorted(applicants_data, key=lambda x: x['score'], reverse=True)[:10],
    }
    
    return render(request, 'job_analytics.html', context)

