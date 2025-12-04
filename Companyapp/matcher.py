import re
from difflib import SequenceMatcher

def fuzzy_match(skill_required, skill_candidate, threshold=0.8):
    """
    Returns True if skills are similar enough.
    Example: 'JavaScript' matches 'Javascript', 'JS'
    """
    skill_req = skill_required.lower().strip()
    skill_can = skill_candidate.lower().strip()
    
    # Exact match
    if skill_req == skill_can:
        return True
    
    # One contains the other (e.g., 'react' in 'react.js')
    if skill_req in skill_can or skill_can in skill_req:
        return True
    
    # Similarity ratio
    ratio = SequenceMatcher(None, skill_req, skill_can).ratio()
    return ratio >= threshold

def calculate_match_percentage(job_advert, resume_data, linkedin_data=None):
    """
    Compares JobAdvertised requirements vs. Resume Extraction data.
    Returns a detailed score breakdown.
    """
    breakdown = {
        'total_score': 0,
        'skills_score': 0,
        'experience_score': 0,
        'education_score': 0,
        'matched_skills': [],
        'missing_skills': [],
        'candidate_years': 0,
        'required_years': 0
    }

    # ==============================
    # 1. SKILLS MATCHING (Weight: 40%)
    # ==============================
    required_skills = [
        s.strip().lower() 
        for s in job_advert.required_skills.split(',') 
        if s.strip()
    ]
    
    candidate_skills = [
        s.lower().strip() 
        for s in resume_data.get('skills', []) 
        if s.strip()
    ]
    
    # Merge LinkedIn skills
    if linkedin_data and 'skills' in linkedin_data:
        candidate_skills += [
            s.lower().strip() 
            for s in linkedin_data['skills'] 
            if s.strip()
        ]
    
    # Remove duplicates
    candidate_skills = list(set(candidate_skills))

    if required_skills:
        matched_skills = []
        
        for req_skill in required_skills:
            # Check for exact or fuzzy match
            for can_skill in candidate_skills:
                if fuzzy_match(req_skill, can_skill):
                    matched_skills.append(req_skill)
                    break
        
        breakdown['matched_skills'] = matched_skills
        breakdown['missing_skills'] = [
            s for s in required_skills 
            if s not in matched_skills
        ]
        
        skill_score = (len(matched_skills) / len(required_skills)) * 100
        breakdown['skills_score'] = round(skill_score, 1)
        breakdown['total_score'] += skill_score * 0.40
    else:
        # No skills required = full points
        breakdown['skills_score'] = 100
        breakdown['total_score'] += 40

    # ==============================
    # 2. EXPERIENCE MATCHING (Weight: 30%)
    # ==============================
    required_years = job_advert.min_experience_years
    candidate_years = 0

    # Extract years from work experience entries
    for job_entry in resume_data.get('work_experience', []):
        # Pattern 1: "Software Dev (2 Years)"
        years_pattern1 = re.findall(r'\((\d+)\s*Years?\)', job_entry, re.IGNORECASE)
        if years_pattern1:
            candidate_years += int(years_pattern1[0])
            continue
        
        # Pattern 2: "Started 2020" (assume 1 year)
        if 'started' in job_entry.lower():
            candidate_years += 1
            continue
        
        # Pattern 3: Look for year ranges "2020-2023"
        year_range = re.findall(r'20\d{2}\s*-\s*20\d{2}', job_entry)
        if year_range:
            years = re.findall(r'20\d{2}', year_range[0])
            if len(years) == 2:
                candidate_years += int(years[1]) - int(years[0])
    
    # Add LinkedIn experience if available
    if linkedin_data and 'years_experience' in linkedin_data:
        candidate_years += linkedin_data['years_experience']
    
    breakdown['candidate_years'] = candidate_years
    breakdown['required_years'] = required_years
    
    if required_years > 0:
        if candidate_years >= required_years:
            exp_score = 100
        else:
            # Partial credit with diminishing returns
            exp_score = min((candidate_years / required_years) * 100, 100)
        
        breakdown['experience_score'] = round(exp_score, 1)
        breakdown['total_score'] += exp_score * 0.30
    else:
        breakdown['experience_score'] = 100
        breakdown['total_score'] += 30

    # ==============================
    # 3. EDUCATION MATCHING (Weight: 30%)
    # ==============================
    edu_levels = {
        'Certificate': 1, 
        'Diploma': 2, 
        'Bachelor': 3, 
        'Master': 4, 
        'PhD': 5
    }
    
    req_level = edu_levels.get(job_advert.required_education, 1)
    candidate_max_level = 0
    candidate_education = resume_data.get('education', [])
    
    # Parse education entries
    for edu in candidate_education:
        if not edu:
            continue
            
        edu_lower = edu.lower()
        
        # Check from highest to lowest
        if any(term in edu_lower for term in ['phd', 'doctorate', 'doctoral']):
            candidate_max_level = max(candidate_max_level, 5)
        elif any(term in edu_lower for term in ['master', 'msc', 'ma', 'mba']):
            candidate_max_level = max(candidate_max_level, 4)
        elif any(term in edu_lower for term in ['bachelor', 'bsc', 'ba', 'b.sc', 'b.a', 'degree']):
            candidate_max_level = max(candidate_max_level, 3)
        elif 'diploma' in edu_lower:
            candidate_max_level = max(candidate_max_level, 2)
        elif 'certificate' in edu_lower:
            candidate_max_level = max(candidate_max_level, 1)

    breakdown['candidate_education_level'] = candidate_max_level
    breakdown['required_education_level'] = req_level
    
    if candidate_max_level >= req_level:
        edu_score = 100
    elif candidate_max_level == req_level - 1:
        # Close but not quite (e.g., Diploma when Bachelor required)
        edu_score = 50
    else:
        # Significantly underqualified
        edu_score = 0
    
    breakdown['education_score'] = round(edu_score, 1)
    breakdown['total_score'] += edu_score * 0.30

    # Final score
    breakdown['total_score'] = round(breakdown['total_score'], 1)
    
    return breakdown


def get_match_rating(score):
    """
    Convert numerical score to qualitative rating.
    """
    if score >= 80:
        return "Excellent Match"
    elif score >= 60:
        return "Good Match"
    elif score >= 40:
        return "Fair Match"
    else:
        return "Poor Match"