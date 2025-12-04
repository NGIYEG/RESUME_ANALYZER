from celery import shared_task
from django.conf import settings
import os
import fitz  # PyMuPDF
from Applicantapp.models import Applicant
from Extractionapp.models import ResumeExtraction
import easyocr

# Initialize reader once at module level (when worker starts)
# This prevents reloading the model for every task
print("🚀 [Celery] Initializing EasyOCR Reader...")
READER = easyocr.Reader(['en'], gpu=False)

@shared_task
def process_resume_task(applicant_id):
    """
    Process resume: Extract text via OCR and analyze with NLP.
    Returns status message.
    """
    try:
        print(f"🚀 [Celery] Processing Applicant ID: {applicant_id}")
        
        applicant = Applicant.objects.get(applicant_id=applicant_id)
        
        # Create or get extraction record
        extraction, created = ResumeExtraction.objects.get_or_create(
            applicant=applicant,
            defaults={'processed': False}
        )
        
        # === STEP 1: PDF to Images ===
        pdf_path = applicant.resume.path
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"Resume file not found: {pdf_path}")
            
        output_folder = os.path.join(
            settings.MEDIA_ROOT, 
            "resume_images", 
            str(applicant.applicant_id)
        )
        os.makedirs(output_folder, exist_ok=True)

        doc = fitz.open(pdf_path)
        image_paths = []
        full_text = ""

        # === STEP 2: OCR Each Page ===
        for page_num in range(len(doc)):
            try:
                page = doc.load_page(page_num)
                
                # Scale 2x for better OCR accuracy
                mat = fitz.Matrix(2.0, 2.0)
                pix = page.get_pixmap(matrix=mat)
                
                img_name = f"page_{page_num+1}.jpg"
                img_path = os.path.join(output_folder, img_name)
                pix.save(img_path)
                
                image_paths.append(
                    f"resume_images/{applicant.applicant_id}/{img_name}"
                )

                # Run OCR on this page
                print(f"   📄 Reading Text on Page {page_num+1}...")
                result = READER.readtext(img_path, detail=0)
                page_text = "\n".join(result)
                full_text += page_text + "\n\n"
                
            except Exception as page_error:
                print(f"⚠️ [Celery] Error on page {page_num+1}: {page_error}")
                # Continue processing other pages
                continue

        doc.close()

        # Save extracted text even if NLP fails
        extraction.extracted_text = full_text
        applicant.converted_images = image_paths
        applicant.save()

        if not full_text.strip():
            extraction.processed = False
            extraction.save()
            return "Warning: No text extracted from resume"

        # === STEP 3: NLP Analysis ===
        try:
            # Lazy import to avoid loading model at Django startup
            from extract_insights import extract_insights
            
            print("   🧠 Running NLP Analysis...")
            insights = extract_insights(full_text)

            # Update extraction record
            extraction.skills = insights.get("skills", [])
            extraction.work_experience = insights.get("work_experience", [])
            extraction.projects = insights.get("projects", [])
            extraction.education = insights.get("education", [])
            extraction.processed = True
            extraction.save()

            print(f"✅ [Celery] Success! Extracted {len(full_text)} characters.")
            print(f"   📊 Skills: {len(insights.get('skills', []))}, "
                  f"Experience: {len(insights.get('work_experience', []))}, "
                  f"Education: {len(insights.get('education', []))}")
            
            return "Success"
            
        except Exception as nlp_error:
            print(f"⚠️ [Celery] NLP Error: {nlp_error}")
            extraction.processed = False
            extraction.save()
            return f"Partial: OCR succeeded, NLP failed: {nlp_error}"

    except Applicant.DoesNotExist:
        error_msg = f"Applicant {applicant_id} not found"
        print(f"💥 [Celery] {error_msg}")
        return error_msg
        
    except Exception as e:
        print(f"💥 [Celery] Critical Error: {e}")
        # Try to save error state
        try:
            extraction = ResumeExtraction.objects.get(applicant_id=applicant_id)
            extraction.processed = False
            extraction.save()
        except:
            pass
        return f"Failed: {e}"