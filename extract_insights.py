import re
from datetime import datetime
from transformers import pipeline

_nlp_pipeline = None

def get_nlp_pipeline():
    global _nlp_pipeline
    if _nlp_pipeline is None:
        print("   🧠 [System] Loading Flan-T5 Model...")
        _nlp_pipeline = pipeline("text2text-generation", model="google/flan-t5-base") 
    return _nlp_pipeline

def smart_split(text):
    """
    Splits text by Commas, Newlines, Bullets, or Semicolons.
    Handles cases where AI forgets commas.
    """
    tokens = re.split(r'[,|\n|•|;|\|]', text)
    return [t.strip() for t in tokens if t.strip()]

def extract_insights(text):
    nlp = get_nlp_pipeline()
    
    # Pre-cleaning: Normalize text
    clean_text = text.replace("\n", ", ").strip()[:3000]

    print("   🧠 [Debug] Asking AI for extraction...")

    # --- Q1: SKILLS ---
    raw_skills = nlp(
        f"Extract only technical skills, tools, programming languages, frameworks (comma-separated list):\n{clean_text}", 
        max_length=150
    )[0]["generated_text"]

    # --- Q2: EDUCATION ---
    raw_education = nlp(
        f"Extract only university names, degree names, field of study (comma-separated):\n{clean_text}", 
        max_length=150
    )[0]["generated_text"]

    # --- Q3: EXPERIENCE ---
    raw_experience = nlp(
        f"List all job positions with company names and years worked. Format: Title at Company (Year-Year):\n{clean_text}", 
        max_length=400
    )[0]["generated_text"]

    # =========================================
    # 🧹 ADVANCED CLEANING ENGINES
    # =========================================
    
    def clean_skills(raw_text):
        """Extract only technical keywords, remove descriptions"""
        cleaned = []
        
        # Blacklist: Common non-skill words
        blacklist = [
            "responsible", "experience", "collaborating", "team", "strong", "working",
            "bachelor", "bsc", "degree", "university", "summary", "profile", "oversee",
            "progress", "project", "developer", "academy", "present", "started", "years",
            "digital", "information", "delivery", "communication", "thinking", "management",
            "designer", "effective", "critical", "founder", "phone", "currently", "lead",
            "designing", "wireframes", "references", "kilifi", "couty", "mitigation",
            "associate", "compiling", "sorting", "data", "july", "processing", "planning",
            "food", "distribution", "knbs", "census", "enumerator", "prelisting",
            "enumeration", "leadership", "jhub", "africa", "entry", "reference", "dr",
            "skills", "software", "development"
        ]
        
        # Known technical terms (whitelist for common skills)
        tech_keywords = [
            "python", "java", "javascript", "react", "node", "sql", "aws", "docker",
            "kubernetes", "git", "api", "html", "css", "typescript", "mongodb", "postgres",
            "excel", "powerpoint", "tableau", "figma", "sketch", "adobe", "photoshop"
        ]
        
        # Regex patterns to reject
        reject_patterns = [
            r'^\d{4}$',  # Standalone years like "2020"
            r'^[A-Z][a-z]+ [A-Z][a-z]+$'  # Full names like "Lawrence Nderu"
        ]
        
        for item in smart_split(raw_text):
            item_lower = item.lower()
            words = item.split()
            
            # Rule 1: Must be 1-3 words
            if not (1 <= len(words) <= 3):
                continue
            
            # Rule 2: Reject based on patterns
            should_reject = False
            for pattern in reject_patterns:
                if re.match(pattern, item.strip()):
                    should_reject = True
                    break
            
            if should_reject:
                continue
            
            # Rule 3: Check if it's a tech term OR doesn't contain blacklist words
            is_tech = any(tech in item_lower for tech in tech_keywords)
            has_bad_word = any(bad in item_lower for bad in blacklist)
            
            if is_tech or (not has_bad_word and len(item) >= 3):
                # Clean up formatting
                cleaned_item = item.title().replace("'S", "'s")
                if cleaned_item not in cleaned:
                    cleaned.append(cleaned_item)
        
        return cleaned[:12]  # Limit to top 12 skills

    def clean_education(raw_text):
        """Extract meaningful education entries only"""
        cleaned = []
        
        # Education indicators
        edu_keywords = ["university", "college", "degree", "bsc", "bachelor", "master", 
                       "diploma", "certificate", "academy", "b.sc", "m.sc", "phd", "msc"]
        
        # Blacklist
        bad_words = ["oversee", "progress", "team", "lead", "project", "kilifi", 
                    "mitigation", "data", "experience", "currently", "designer",
                    "developer", "user", "wireframes"]
        
        for item in smart_split(raw_text):
            item_lower = item.lower()
            
            # Must contain education keyword
            if not any(k in item_lower for k in edu_keywords):
                continue
            
            # Must not contain bad words
            if any(bad in item_lower for bad in bad_words):
                continue
            
            # Remove year mentions if they appear alone
            item_clean = re.sub(r'\b(19|20)\d{2}\b', '', item).strip()
            
            # Must have meaningful length
            if len(item_clean) > 4 and item_clean not in cleaned:
                # Capitalize properly
                item_clean = item_clean.replace("bsc", "BSc").replace("msc", "MSc")
                cleaned.append(item_clean)
        
        # If nothing found, try extracting from original text with better regex
        if not cleaned:
            # Try to find "BSc Computer Science" patterns
            degree_patterns = [
                r'(B\.?Sc\.?\s+[\w\s]+?)(?=,|\.|$)',
                r'(Bachelor[\w\s]+?)(?=,|\.|from|$)',
                r'(Master[\w\s]+?)(?=,|\.|from|$)',
                r'(Diploma[\w\s]+?)(?=,|\.|from|$)'
            ]
            
            for pattern in degree_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches[:2]:
                    clean_match = match.strip()
                    if len(clean_match) > 8:
                        cleaned.append(clean_match)
        
        return cleaned[:5]  # Limit to 5 education entries

    def calculate_experience_chopper(raw_text):
        """Extract clean job titles with calculated duration"""
        processed_jobs = []
        current_year = datetime.now().year
        
        # Blacklist words that indicate we're reading non-job descriptions
        job_blacklist = ["bsc", "bachelor", "degree", "university", "academy", "college",
                        "oversee", "designing", "wireframes", "progress"]

        for item in smart_split(raw_text):
            if len(item) < 5:
                continue
            
            # Skip if contains education keywords
            item_lower = item.lower()
            if any(bad in item_lower for bad in job_blacklist):
                continue

            # 1. EXTRACT JOB TITLE (before any year or description)
            title_parts = re.split(r'\d{4}', item)
            title_only = title_parts[0].strip() if title_parts else item
            
            # Remove common description triggers
            split_words = [" with ", " at ", " for ", " responsible ", " adept ", 
                          " working ", " using ", " expertise ", " overseeing ", 
                          " designing ", " known ", " committed "]
            
            for sword in split_words:
                if sword.lower() in title_only.lower():
                    title_only = title_only.lower().split(sword)[0].strip()
                    break
            
            # Clean parentheses and extra punctuation
            title_only = re.sub(r'[(),]', '', title_only).strip()
            
            # Remove trailing words that indicate description started
            desc_words = ["oversee", "design", "data", "currently", "bsc", "known", "focus"]
            words = title_only.split()
            clean_words = []
            for word in words:
                if any(desc in word.lower() for desc in desc_words):
                    break
                clean_words.append(word)
            
            title_only = " ".join(clean_words)
            
            # Skip if title is too short or contains only common words
            if len(title_only.split()) < 2:
                continue
            
            # Limit to 6 words max for job titles
            words = title_only.split()
            if len(words) > 6:
                short_title = " ".join(words[:6])
            else:
                short_title = title_only

            # 2. CALCULATE YEARS OF EXPERIENCE FROM ORIGINAL ITEM
            years_found = re.findall(r'20\d{2}', item)
            years_found = [int(y) for y in years_found if 2000 <= int(y) <= current_year + 5]  # Allow future dates
            
            duration_str = ""
            if years_found:
                is_current = "present" in item.lower() or "now" in item.lower() or "current" in item.lower()
                
                if is_current and len(years_found) >= 1:
                    start = min(years_found)
                    diff = current_year - start
                    if diff > 0:
                        duration_str = f"({diff} yrs)"
                    else:
                        duration_str = "(Current)"
                elif len(years_found) >= 2:
                    start_year = min(years_found)
                    end_year = max(years_found)
                    diff = end_year - start_year
                    if diff > 0:
                        duration_str = f"({start_year}-{end_year}, {diff} yrs)"
                    else:
                        duration_str = f"({start_year})"
                else:
                    duration_str = f"(Since {years_found[0]})"

            # 3. BUILD FINAL STRING - Must have reasonable title
            if short_title and len(short_title) > 3:
                # Skip if title contains numbers
                if any(char.isdigit() for char in short_title):
                    continue
                    
                formatted_title = short_title.title()
                
                # Build final entry
                if duration_str:
                    final_entry = f"{formatted_title} {duration_str}"
                else:
                    final_entry = formatted_title
                
                # Avoid duplicates
                if final_entry not in processed_jobs:
                    processed_jobs.append(final_entry)
        
        # FALLBACK: If no jobs extracted, try to extract from original text directly
        if not processed_jobs:
            # Look for patterns like "JHUB AFRICA 2023-PRESENT"
            work_patterns = re.findall(r'([A-Z\s]{4,30})\s*(20\d{2})(?:\s*-\s*(PRESENT|20\d{2}))?', text)
            for match in work_patterns[:5]:
                title, start_year, end_year = match
                title = title.strip().title()
                
                # Skip education keywords
                if any(edu in title.lower() for edu in ["education", "university", "academy", "degree"]):
                    continue
                
                start = int(start_year)
                if end_year and end_year.upper() == "PRESENT":
                    duration = current_year - start
                    processed_jobs.append(f"{title} ({duration} yrs)")
                elif end_year:
                    duration = int(end_year) - start
                    if duration > 0:
                        processed_jobs.append(f"{title} ({start}-{end_year}, {duration} yrs)")
                else:
                    processed_jobs.append(f"{title} (Since {start})")

        return processed_jobs[:8]  # Limit to 8 most relevant experiences

    # =========================================
    # 📊 EXTRACT ADDITIONAL INSIGHTS + DIRECT PARSING
    # =========================================
    
    def extract_work_from_raw_text(text):
        """Directly extract work experience from OCR text (more reliable than AI)"""
        work_entries = []
        current_year = datetime.now().year
        
        # Pattern 1: "JHUB AFRICA\n2023-PRESENT"
        pattern1 = re.findall(r'([A-Z][A-Za-z\s&]{3,30})\s*\n?\s*(20\d{2})\s*-?\s*(PRESENT|20\d{2})?', text, re.MULTILINE)
        
        for match in pattern1:
            company, start_year, end_info = match
            company = company.strip().title()
            
            # Skip if it's an education institution
            edu_keywords = ["university", "academy", "college", "education"]
            if any(edu in company.lower() for edu in edu_keywords):
                continue
            
            start = int(start_year)
            
            if end_info.upper() == "PRESENT" or "PRESENT" in text[text.find(start_year):text.find(start_year)+50]:
                duration = current_year - start
                if duration > 0:
                    work_entries.append(f"{company} ({duration} yrs)")
                else:
                    work_entries.append(f"{company} (Current)")
            elif end_info and end_info.isdigit():
                end = int(end_info)
                duration = end - start
                if duration > 0:
                    work_entries.append(f"{company} ({start}-{end}, {duration} yrs)")
            else:
                work_entries.append(f"{company} (Since {start})")
        
        # Pattern 2: Look for "WORK" or "EXPERIENCE" section
        work_section = re.search(r'WORK.*?EXPERIENCE(.*?)(?:EDUCATION|SKILLS|$)', text, re.DOTALL | re.IGNORECASE)
        if work_section:
            section_text = work_section.group(1)
            # Extract company-year pairs from this section
            companies = re.findall(r'([A-Z][A-Za-z\s&]{3,25})\s*(20\d{2})\s*-?\s*(PRESENT|20\d{2})?', section_text)
            for company, start_year, end_info in companies[:5]:
                company = company.strip().title()
                start = int(start_year)
                
                if end_info.upper() == "PRESENT":
                    duration = current_year - start
                    entry = f"{company} ({duration} yrs)" if duration > 0 else f"{company} (Current)"
                elif end_info and end_info.isdigit():
                    duration = int(end_info) - start
                    entry = f"{company} ({start}-{end_info}, {duration} yrs)" if duration > 0 else f"{company} ({start})"
                else:
                    entry = f"{company} (Since {start})"
                
                if entry not in work_entries:
                    work_entries.append(entry)
        
        return work_entries[:6]
    
    def extract_contact_info(text):
        """Extract email and phone"""
        email = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        phone = re.search(r'\+?\d{1,4}[\s-]?\d{3}[\s-]?\d{3}[\s-]?\d{3,4}', text)
        
        return {
            "email": email.group(0) if email else None,
            "phone": phone.group(0) if phone else None
        }
    
    def extract_projects(text):
        """Look for project keywords"""
        project_keywords = ["project", "initiative", "poliagentx", "jhub", "africa"]
        projects = []
        
        for keyword in project_keywords:
            pattern = rf'({keyword}[\w\s]+?)(?:[.,;]|\n|$)'
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) > 5 and len(match) < 100:
                    projects.append(match.strip().title())
        
        return list(set(projects))[:5]

    # =========================================
    # 🎯 RETURN STRUCTURED DATA
    # =========================================
    
    contact = extract_contact_info(text)
    
    # Try direct parsing first for work experience (more reliable)
    direct_work = extract_work_from_raw_text(text)
    ai_work = calculate_experience_chopper(raw_experience)
    
    # Combine and deduplicate, prioritizing direct extraction
    combined_work = direct_work.copy()
    for ai_entry in ai_work:
        if ai_entry not in combined_work and len(combined_work) < 8:
            combined_work.append(ai_entry)
    
    return {
        "contact": contact,
        "skills": clean_skills(raw_skills),
        "education": clean_education(raw_education),
        "work_experience": combined_work if combined_work else ai_work,
        "projects": extract_projects(text)
    }