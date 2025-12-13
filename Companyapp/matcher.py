import re
from datetime import datetime
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer, util

# Global cache for the AI model to prevent reloading it on every request
_semantic_model = None

def get_semantic_model():
    global _semantic_model
    if _semantic_model is None:
        print("   🧠 [System] Loading Semantic Matching Model (all-MiniLM-L6-v2)...")
        _semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _semantic_model

def get_similarity_score(text1, text2):
    """
    Calculates semantic similarity between two texts (0 to 1).
    Uses AI to understand that 'Coder' is similar to 'Developer'.
    """
    model = get_semantic_model()
    # Encode sentences to get their embeddings
    emb1 = model.encode(text1, convert_to_tensor=True)
    emb2 = model.encode(text2, convert_to_tensor=True)
    # Compute cosine similarity
    return float(util.pytorch_cos_sim(emb1, emb2)[0][0])

def parse_years_from_entry(entry):
    """
    Extracts duration from job entries like:
    - "Software Engineer (2 yrs)"
    - "DevOps (2019-2022)"
    - "Manager (2020-Present)"
    """
    current_year = datetime.now().year
    text = entry.lower()

    # Case 1: Explicit "(2 years)"
    match = re.search(r'\b(\d+)\s*(?:yr|yrs|year|years)\b', text)
    if match:
        years = int(match.group(1))
        # Sanity check: ignore unrealistic durations (>40 years)
        if 0 < years <= 40:
            return years

    # Case 2: Year Range "2019 - 2022"
    range_match = re.findall(r'(20\d{2})\s*[-/–]\s*(20\d{2})', text)
    if range_match:
        start, end = map(int, range_match[-1])
        return max(1, end - start)

    # Case 3: "2020 - Present"
    years_found = re.findall(r'20\d{2}', text)
    if years_found and any(k in text for k in ['present', 'current', 'now']):
        start = int(years_found[0])
        return max(1, current_year - start)

    return 0

def clean_title_for_matching(entry):
    """
    Cleans a job entry to isolate the job title for AI comparison.
    Input: "Senior Developer at Google (2020-2022)"
    Output: "Senior Developer"
    """
    t = entry.lower()
    # Remove content in parentheses
    t = re.sub(r'\(.*?\)', '', t)
    # Remove years
    t = re.sub(r'\b20\d{2}\b', '', t)
    # Remove standard stop words
    for stop_word in [" at ", " with ", " for ", " in ", " on "]:
        if stop_word in t:
            t = t.split(stop_word)[0]
    return t.strip().title()

def match_academic_courses(job_courses, candidate_education, threshold=0.75):
    """
    Matches specific academic courses (e.g., 'Computer Science').
    Uses fuzzy string matching.
    """
    if not job_courses or not candidate_education:
        return {'matched_courses': [], 'match_percentage': 100.0 if not job_courses else 0.0}
    
    matched_courses = []
    job_courses_normalized = [course.lower().strip() for course in job_courses]
    education_text = " ".join(candidate_education).lower()
    
    for idx, course in enumerate(job_courses):
        course_lower = job_courses_normalized[idx]
        
        # Direct or Fuzzy match found in education text
        if course_lower in education_text:
            matched_courses.append(course)
        else:
            # Check individual education entries
            for edu_entry in candidate_education:
                if SequenceMatcher(None, course_lower, edu_entry.lower()).ratio() >= threshold:
                    matched_courses.append(course)
                    break
    
    match_percentage = (len(matched_courses) / len(job_courses)) * 100
    return {
        'matched_courses': list(set(matched_courses)),
        'match_percentage': round(match_percentage, 1)
    }

def calculate_match_percentage(job_advert, resume_data, linkedin_data=None, job_courses=None):
    """
    HYBRID MATCHING ENGINE
    
    Weights:
    - Skills: 80% (Semantic AI Match)
    - Experience: 10% (Context-Aware AI Match)
    - Education: 10% (Strict Hierarchy)
    """
    
    target_role = job_advert.post.title
    resume_jobs = resume_data.get("work_experience", [])
    
    breakdown = {
        'total_score': 0,
        'skills_score': 0,
        'experience_score': 0,
        'education_score': 0,
        'course_match_score': 0,
        'matched_skills': [],
        'missing_skills': [],
        'matched_courses': [],
        'candidate_years': 0,
        'required_years': 0
    }

    # ==========================================
    # 1. EXPERIENCE MATCHING (10%) - AI Powered
    # ==========================================
    total_relevant_years = 0
    required_years = job_advert.min_experience_years

    # Only count years if the job title is semantically similar to the target role
    for job_entry in resume_jobs:
        job_title = clean_title_for_matching(job_entry)
        years = parse_years_from_entry(job_entry)
        
        # AI Similarity Check (Threshold 0.45 usually catches 'Dev' vs 'Engineer')
        if get_similarity_score(target_role, job_title) >= 0.45:
            total_relevant_years += years

    # Add LinkedIn years if available (assume they are relevant for now)
    if linkedin_data and 'years_experience' in linkedin_data:
        total_relevant_years += linkedin_data['years_experience']

    breakdown['candidate_years'] = total_relevant_years
    breakdown['required_years'] = required_years

    if required_years > 0:
        if total_relevant_years >= required_years:
            exp_score = 100
        else:
            exp_score = min(round((total_relevant_years / required_years) * 100), 100)
    else:
        exp_score = 100
    
    breakdown['experience_score'] = exp_score
    breakdown['total_score'] += exp_score * 0.10

    # ==========================================
    # 2. SKILLS MATCHING (80%) - AI Powered
    # ==========================================
    req_skills = [s.strip().lower() for s in job_advert.required_skills.split(",") if s.strip()]
    cand_skills = [s.lower() for s in resume_data.get("skills", [])]
    
    if linkedin_data and 'skills' in linkedin_data:
        cand_skills += [s.lower() for s in linkedin_data['skills']]

    matched_skills = []
    
    if req_skills:
        for req in req_skills:
            # Check for exact match first (fast)
            if any(req in cs for cs in cand_skills):
                matched_skills.append(req)
                continue
            
            # Fallback to AI Semantic Match (slower but smarter)
            # Checks if 'req' is similar to any 'cand_skill'
            best_match_score = 0
            for cs in cand_skills:
                score = get_similarity_score(req, cs)
                if score > best_match_score:
                    best_match_score = score
            
            # Threshold 0.6 is good for short text similarity
            if best_match_score >= 0.6:
                matched_skills.append(req)

        breakdown['matched_skills'] = matched_skills
        breakdown['missing_skills'] = [s for s in req_skills if s not in matched_skills]
        
        skills_score = round((len(matched_skills) / len(req_skills)) * 100)
        breakdown['skills_score'] = skills_score
        breakdown['total_score'] += skills_score * 0.80
    else:
        breakdown['skills_score'] = 100
        breakdown['total_score'] += 80

    # ==========================================
    # 3. EDUCATION MATCHING (10%) - Strict
    # ==========================================
    edu_levels = {
        "certificate": 1, 
        "diploma": 2, "associate": 2, "hnd": 2,
        "bachelor": 3, "degree": 3, "bsc": 3, "b.sc": 3, "undergraduate": 3,
        "master": 4, "msc": 4, "mba": 4, "postgraduate": 4,
        "phd": 5, "doctorate": 5
    }

    # Determine Required Level
    req_str = job_advert.required_education.lower()
    req_level = 1
    for key, val in edu_levels.items():
        if key in req_str:
            req_level = max(req_level, val)

    # Determine Candidate Level
    cand_max_level = 0
    for edu in resume_data.get("education", []):
        e_lower = edu.lower()
        for key, val in edu_levels.items():
            if key in e_lower:
                cand_max_level = max(cand_max_level, val)

    breakdown['required_education_level'] = req_level
    breakdown['candidate_education_level'] = cand_max_level

    # Strict Logic: Must be >= Required
    if cand_max_level >= req_level:
        edu_score = 100
    else:
        edu_score = 0

    breakdown['education_score'] = edu_score
    breakdown['total_score'] += edu_score * 0.10

    # ==========================================
    # 4. ACADEMIC COURSE MATCHING (0%)
    # ==========================================
    # Logic runs to populate display data, but adds 0 to score
    if job_courses:
        course_results = match_academic_courses(job_courses, resume_data.get("education", []))
        breakdown['matched_courses'] = course_results['matched_courses']
        breakdown['course_match_score'] = course_results['match_percentage']
    else:
        breakdown['course_match_score'] = 100

    # Final Rounding
    breakdown['total_score'] = round(breakdown['total_score'], 1)

    return breakdown

def get_match_rating(score):
    if score >= 80: return "Excellent Match"
    elif score >= 60: return "Good Match"
    elif score >= 40: return "Fair Match"
    else: return "Poor Match"