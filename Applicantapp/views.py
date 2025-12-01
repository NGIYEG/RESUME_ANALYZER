
from django.shortcuts import render, redirect
from .forms import ApplicantApplyForm
from Companyapp.models import Application, JobAdvertised
from django.contrib import messages
import fitz  # PyMuPDF
import os
from django.conf import settings
# Create your views here.

def apply_for_job(request):
    if request.method == "POST":
        form = ApplicantApplyForm(request.POST, request.FILES)
        if form.is_valid():
            applicant = form.save()

            # create application entry
            job_advert = form.cleaned_data['job']
            Application.objects.create(
                applicant=applicant,
                post=job_advert.post
            )

            # -----------------------------------------
            # Convert PDF Resume → Images (PyMuPDF)
            # -----------------------------------------
            pdf_path = applicant.resume.path

            # Folder to save images
            output_folder = os.path.join(
                settings.MEDIA_ROOT,
                "resume_images",
                str(applicant.applicant_id)
            )
            os.makedirs(output_folder, exist_ok=True)

            doc = fitz.open(pdf_path)
            image_paths = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                pix = page.get_pixmap(dpi=150)   # good quality for text
                img_filename = f"page_{page_num + 1}.jpg"
                img_path = os.path.join(output_folder, img_filename)

                pix.save(img_path)

                # Add path relative to MEDIA_URL
                image_paths.append(f"resume_images/{applicant.applicant_id}/{img_filename}")

            # Save list of images to DB
            applicant.converted_images = image_paths
            applicant.save()

            messages.success(request, "Your application has been submitted successfully!")
            return redirect("apply_job")

    else:
        form = ApplicantApplyForm()

    jobs = JobAdvertised.objects.all()
    return render(request, "job_application.html", {"form": form, "jobs": jobs})
