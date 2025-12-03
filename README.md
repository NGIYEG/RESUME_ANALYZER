# 🎯 Resume Analyzer - AI-Powered Recruitment System

An intelligent Django-based application that automates resume screening using OCR and NLP to match candidates with job requirements.

## ✨ Features

- **📄 Automated Resume Processing**: Upload PDF resumes and extract text using EasyOCR
- **🤖 AI-Powered Analysis**: Extract skills, experience, education, and projects using Flan-T5
- **📊 Smart Matching Algorithm**: Calculate candidate-job match scores (0-100%)
- **⚡ Asynchronous Processing**: Background task processing with Celery
- **📈 Analytics Dashboard**: Visualize applicant statistics and trends
- **🎨 Modern UI**: Beautiful Tailwind CSS interface
- **🔍 Fuzzy Skill Matching**: Match similar skills (e.g., "Python" ≈ "python" ≈ "py")

## 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Applicant │────▶│    Django    │────▶│    Redis    │
│   Uploads   │     │  Web Server  │     │   (Broker)  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                     │
                            │                     ▼
                            │              ┌─────────────┐
                            │              │   Celery    │
                            │              │   Worker    │
                            │              └─────────────┘
                            │                     │
                            ▼                     ▼
                     ┌──────────────┐    ┌──────────────┐
                     │  PostgreSQL  │◀───│   EasyOCR    │
                     │  (Database)  │    │  + Flan-T5   │
                     └──────────────┘    └──────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Redis Server
- Node.js (for Tailwind CSS)
- 4GB+ RAM (for ML models)

### 1. Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd Resumeanalyzer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run setup script
python setup.py
```

### 2. Configuration

Update `.env` file with your settings:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
REDIS_URL=redis://localhost:6379/0
```

### 3. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run the Application

**Terminal 1 - Redis:**
```bash
redis-server
```

**Terminal 2 - Celery Worker:**
```bash
# Windows
celery -A Resumeanalyzer worker --loglevel=info --pool=solo

# Linux/Mac
celery -A Resumeanalyzer worker --loglevel=info
```

**Terminal 3 - Django Server:**
```bash
python manage.py runserver
```

Visit: http://localhost:8000

## 📁 Project Structure

```
Resumeanalyzer/
├── Applicantapp/          # Job application & resume upload
│   ├── models.py         # Applicant model
│   ├── views.py          # Application views
│   ├── forms.py          # Application form
│   ├── tasks.py          # Celery tasks (OCR + NLP)
│   └── urls.py
├── Companyapp/           # Job posting & applicant review
│   ├── models.py         # Job, Department, Application models
│   ├── views.py          # Job management views
│   ├── matcher.py        # Matching algorithm
│   └── urls.py
├── Extractionapp/        # Resume data extraction
│   └── models.py         # ResumeExtraction model
├── Analyzerapp/          # Analytics & dashboard
│   ├── models.py         # Analytics models
│   ├── views.py          # Dashboard views
│   └── urls.py
├── extract_insights.py   # NLP processing logic
├── media/                # Uploaded files
│   ├── resumes/         # PDF resumes
│   ├── documents/       # Additional documents
│   └── resume_images/   # Extracted images
├── templates/            # HTML templates
├── static/              # Static files
├── requirements.txt     # Python dependencies
└── setup.py            # Automated setup script
```

## 🎯 Usage Guide

### For HR Managers

1. **Create Department & Posts**
   - Navigate to: http://localhost:8000/
   - Add departments (e.g., "Engineering", "Marketing")
   - Create job posts within departments

2. **Advertise Job Opening**
   - Go to: http://localhost:8000/advertise-job/
   - Fill in:
     - Job description
     - Required skills (comma-separated)
     - Minimum experience years
     - Required education level
     - Application deadline

3. **Review Applicants**
   - View ranked applicants: http://localhost:8000/job/{job_id}/applicants/
   - See match scores, skills, experience
   - Contact top candidates

4. **Analytics Dashboard**
   - Visit: http://localhost:8000/review_dashboard/
   - View application statistics
   - Analyze skill trends

### For Job Seekers

1. **Apply for Job**
   - Go to: http://localhost:8000/application/apply-job/
   - Fill in personal details
   - Upload PDF resume
   - Submit application

2. **Automatic Processing**
   - System extracts text from resume (30-60 seconds)
   - AI analyzes skills, experience, education
   - Match score calculated automatically

## 🧮 Matching Algorithm

The system calculates a **0-100% match score** based on:

### **Skills (40% weight)**
- Exact matches: +100% for that skill
- Fuzzy matches: e.g., "JavaScript" matches "javascript"
- Final: (matched skills / required skills) × 100 × 0.40

### **Experience (30% weight)**
- Extracts years from resume entries
- Compares with required years
- Partial credit for close matches

### **Education (30% weight)**
- Hierarchy: PhD > Master > Bachelor > Diploma > Certificate
- Full credit if candidate meets or exceeds requirement
- Partial credit for "close" levels

**Example:**
```
Job Requirements:
- Skills: Python, Django, PostgreSQL, Docker
- Experience: 3 years
- Education: Bachelor

Candidate A:
- Skills: Python, Django, PostgreSQL (3/4 = 75%)
- Experience: 4 years (100%)
- Education: Bachelor (100%)
→ Score: (75×0.4) + (100×0.3) + (100×0.3) = 90%

Candidate B:
- Skills: Java, Spring (0/4 = 0%)
- Experience: 1 year (33%)
- Education: Diploma (50%)
→ Score: (0×0.4) + (33×0.3) + (50×0.3) = 24.9%
```

## 🔧 Configuration

### Matching Weights (Companyapp/matcher.py)

```python
SKILL_MATCH_WEIGHT = 0.40      # 40%
EXPERIENCE_MATCH_WEIGHT = 0.30  # 30%
EDUCATION_MATCH_WEIGHT = 0.30   # 30%
```

### OCR Settings (tasks.py)

```python
READER = easyocr.Reader(['en'], gpu=False)
# Change gpu=True if you have CUDA
```

### NLP Model (extract_insights.py)

```python
_nlp_pipeline = pipeline(
    "text2text-generation", 
    model="google/flan-t5-base"
)
# Can use "google/flan-t5-large" for better accuracy
```

## 🧪 Testing

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test Companyapp.tests.test_matcher

# With coverage
coverage run --source='.' manage.py test
coverage report
```

## 📊 Monitoring

### Celery Tasks

```bash
# Monitor tasks with Flower
pip install flower
celery -A Resumeanalyzer flower
# Visit: http://localhost:5555
```

### Redis Queue

```bash
redis-cli
> LLEN celery          # View queue length
> KEYS *               # View all keys
> FLUSHALL             # Clear all data (be careful!)
```

### Django Shell

```python
python manage.py shell

# Check extractions
>>> from Extractionapp.models import ResumeExtraction
>>> ResumeExtraction.objects.filter(processed=True).count()

# View applicant data
>>> from Applicantapp.models import Applicant
>>> applicant = Applicant.objects.first()
>>> extraction = applicant.resumeextraction
>>> print(extraction.skills)
```

## 🐛 Troubleshooting

### Issue: Celery not processing tasks

**Solution:**
```bash
# Check Redis is running
redis-cli ping  # Should return PONG

# Restart Celery with debug logging
celery -A Resumeanalyzer worker --loglevel=debug

# Clear stuck tasks
redis-cli FLUSHALL
```

### Issue: OCR returns empty text

**Causes:**
- Low resolution PDF
- Scanned image quality
- Non-English text

**Solutions:**
```python
# In tasks.py, increase zoom
mat = fitz.Matrix(3.0, 3.0)  # Changed from 2.0
```

### Issue: NLP model fails to load

**Solution:**
```bash
# Reinstall transformers
pip uninstall transformers
pip install transformers==4.36.0

# Test manually
python -c "from transformers import pipeline; nlp = pipeline('text2text-generation', model='google/flan-t5-base')"
```

### Issue: Match scores always 0

**Debug:**
```python
# In Django shell
from Companyapp.matcher import calculate_match_percentage
from Companyapp.models import JobAdvertised
from Extractionapp.models import ResumeExtraction

job = JobAdvertised.objects.first()
extraction = ResumeExtraction.objects.first()

resume_data = {
    'skills': extraction.skills or [],
    'work_experience': extraction.work_experience or [],
    'education': extraction.education or [],
}

result = calculate_match_percentage(job, resume_data)
print(result)  # Check detailed breakdown
```

## 🚀 Deployment

### Production Checklist

- [ ] Set `DEBUG = False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Generate new `SECRET_KEY`
- [ ] Enable HTTPS
- [ ] Set up Gunicorn + Nginx
- [ ] Configure Supervisor for Celery
- [ ] Set up log rotation
- [ ] Enable Redis persistence
- [ ] Configure backups

### Example Deployment (Ubuntu + Nginx + Gunicorn)

```bash
# Install dependencies
sudo apt-get update
sudo apt-get install nginx postgresql redis-server

# Set up Gunicorn
pip install gunicorn
gunicorn Resumeanalyzer.wsgi:application --bind 0.0.0.0:8000

# Configure Nginx (see deployment docs)
sudo nano /etc/nginx/sites-available/resumeanalyzer

# Set up Supervisor for Celery
sudo nano /etc/supervisor/conf.d/celery.conf
sudo supervisorctl reread
sudo supervisorctl update
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Submit pull request

## 📝 License

[Your License Here]

## 👥 Authors

GEORGE OTIENO NGIYE

## 📧 Support

For issues and questions:
- GitHub Issues: https://github.com/NGIYEG/RESUME_ANALYZER.git
- Email: georgengiye3@gmail.com

## 🙏 Acknowledgments

- EasyOCR for OCR capabilities
- Hugging Face for NLP models
- Django & Celery communities

---


